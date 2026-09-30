"""
MilkShield - 2D natural-convection CFD of milk cooling around the cartridges.

Vertical slice through the can (400 mm wide x 512 mm deep milk) cutting two
lid-hung cartridges (80 mm wide, 400 mm long). Boussinesq vorticity /
stream-function solver, semi-implicit diffusion, upwind advection.

HONEST LIMITS
* Real milk convection here is turbulent (Ra ~ 1e10); a 4 mm grid cannot
  resolve that, so we use an EFFECTIVE (eddy) viscosity/diffusivity (Pr_t = 1) giving
  Ra_eff = 1e6. Flow PATTERN (cold plumes, stratification, warm pockets) is
  the useful output; absolute timing depends on that assumption.
* Cartridge surface held at 0 degC (melting ice) behind the HDPE wall +
  internal resistance; heat transfer per unit milk volume is scaled to match
  the 3D can with 8 cartridges (a 2D slice has less cartridge area).
Outputs: cfd_frames.npz (fields over time) -> render with sim4_render.py
"""
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# ---- geometry (m) ----
W, H, h = 0.400, 0.512, 0.004
NX, NZ = int(round(W / h)) + 1, int(round(H / h)) + 1
x = np.arange(NX) * h; z = np.arange(NZ) * h
X, Z = np.meshgrid(x, z)                   # arrays indexed [j(z), i(x)]
CART = [(0.030, 0.110), (0.290, 0.370)]    # x-extent of the two cartridges in the slice
CART_BOTTOM = H - 0.400
obst = np.zeros((NZ, NX), bool)
for a, b in CART:
    obst |= (X >= a - 1e-9) & (X <= b + 1e-9) & (Z >= CART_BOTTOM - 1e-9)
wall = np.zeros((NZ, NX), bool); wall[0, :] = wall[-1, :] = wall[:, 0] = wall[:, -1] = True
fluid = ~obst & ~wall                      # vorticity / psi unknowns
tnode = ~obst                              # temperature unknowns (walls included, Neumann)

# ---- properties ----
RHO, CP = 1032.0, 3930.0
G, BETA = 9.81, 3.0e-4                     # milk ~ water-like expansion (assumed constant)
T0, T_AMB, T_ICE = 35.0, 35.0, 0.0
DT_REF = 35.0
PR, RA = 1.0, 1.0e6                   # turbulent (eddy) Prandtl ~ 1
ALPHA = np.sqrt(G * BETA * DT_REF * H**3 / (PR * RA))   # effective diffusivity
NU = PR * ALPHA
U_WALL = 0.025 / 0.040                     # W/m2K through 40 mm PUF
R_CART = 0.002 / 0.45 + 1 / 200.0          # HDPE wall + ice/meltwater side, m2K/W
area2d = sum(2 * 0.400 + (b - a) for a, b in CART)       # m cartridge surface per m depth
vol2d = W * H - sum((b - a) * 0.400 for a, b in CART)    # m2 milk per m depth
ratio3d = 8 * 0.11 / (40 * 1.0e-3)                       # m2/m3 for 8 cartridges, 40 L
F_SCALE = ratio3d / (area2d / vol2d)
G_CART = F_SCALE / R_CART                  # W/m2K effective cartridge surface conductance

DT = 0.12                                  # keep nu*DT/h^2 < 1 (explicit Thom wall vorticity)
T_END = 2 * 3600.0
SAVE_EVERY = 30.0

def idx_map(mask):
    m = -np.ones(mask.shape, int); m[mask] = np.arange(mask.sum()); return m

# ---- psi Poisson over fluid nodes (psi=0 on walls + cartridges: they hang from the lid) ----
fi = idx_map(fluid); nf = fluid.sum()
jj, ii = np.nonzero(fluid)
rows, cols, vals = [], [], []
NB = ((0, 1), (0, -1), (1, 0), (-1, 0))
for dj, di in NB:
    j2, i2 = jj + dj, ii + di
    m = fluid[j2, i2]
    rows += list(fi[jj, ii][m]); cols += list(fi[j2, i2][m]); vals += [1 / h**2] * int(m.sum())
L = sp.csr_matrix((vals, (rows, cols)), shape=(nf, nf)) - sp.eye(nf) * 4 / h**2
lu_psi = spla.splu(sp.csc_matrix(L))
lu_w = spla.splu(sp.csc_matrix(sp.eye(nf) - DT * NU * L))
# boundary contribution for omega: Dirichlet omega_b at non-fluid neighbours
bnd_pairs = []
for dj, di in NB:
    j2, i2 = jj + dj, ii + di
    m = ~fluid[j2, i2]
    bnd_pairs.append((fi[jj, ii][m], j2[m], i2[m]))

# ---- temperature operator over tnode (Neumann at walls/cartridges, sink at cartridge faces) ----
ti = idx_map(tnode); nt = tnode.sum()
tj, tii = np.nonzero(tnode)
rows, cols, vals = [], [], []
diag = np.zeros(nt); ncart = np.zeros(nt); nwall = np.zeros(nt)
for dj, di in NB:
    j2, i2 = tj + dj, tii + di
    inside = (j2 >= 0) & (j2 < NZ) & (i2 >= 0) & (i2 < NX)
    j2c, i2c = np.clip(j2, 0, NZ - 1), np.clip(i2, 0, NX - 1)
    m = inside & tnode[j2c, i2c]
    rows += list(ti[tj, tii][m]); cols += list(ti[j2c, i2c][m]); vals += [ALPHA / h**2] * int(m.sum())
    diag[m] -= ALPHA / h**2
    ncart += inside & obst[j2c, i2c]
    nwall += ~inside
LT = sp.csr_matrix((vals, (rows, cols)), shape=(nt, nt)) + sp.diags(diag)
sink = ncart * G_CART / (RHO * CP * h)     # 1/s
lu_T = spla.splu(sp.csc_matrix(sp.eye(nt) - DT * (LT - sp.diags(sink))))
wall_src = nwall * U_WALL / (RHO * CP * h) # 1/s towards ambient

# for upwind advection, cartridge-surface nodes borrow a neighbouring milk temperature
surf = obst & (np.roll(tnode, 1, 0) | np.roll(tnode, -1, 0) | np.roll(tnode, 1, 1) | np.roll(tnode, -1, 1))
pairs = []
for j, i in zip(*np.nonzero(surf)):
    for dj, di in NB:
        if 0 <= j + dj < NZ and 0 <= i + di < NX and tnode[j + dj, i + di]:
            pairs.append((j, i, j + dj, i + di)); break
pairs = np.array(pairs); sj, si, src = pairs[:, 0], pairs[:, 1], pairs[:, 2:]

def upwind(f, u, w):
    fxm = (f - np.roll(f, 1, 1)) / h; fxp = (np.roll(f, -1, 1) - f) / h
    fzm = (f - np.roll(f, 1, 0)) / h; fzp = (np.roll(f, -1, 0) - f) / h
    return np.where(u > 0, u * fxm, u * fxp) + np.where(w > 0, w * fzm, w * fzp)

T = np.full((NZ, NX), T0); T[obst] = T_ICE
omega = np.zeros((NZ, NX)); psi = np.zeros((NZ, NX))
frames_T, frames_psi, times, mean_T, top_T, bot_T, umax_log = [], [], [], [], [], [], []
milk = tnode
top_band = milk & (Z > H - 0.10); bot_band = milk & (Z < 0.10)
print(f"grid {NX}x{NZ}, alpha_eff {ALPHA:.2e} m2/s, nu_eff {NU:.2e} m2/s, cartridge conductance x{F_SCALE:.2f} -> {G_CART:.0f} W/m2K")
t, step, t0 = 0.0, 0, time.time()
next_save = 0.0
while t <= T_END + 1e-9:
    if t >= next_save - 1e-9:
        frames_T.append(T.astype(np.float32).copy()); frames_psi.append(psi.astype(np.float32).copy())
        times.append(t); mean_T.append(T[milk].mean()); top_T.append(T[top_band].mean()); bot_T.append(T[bot_band].mean())
        next_save += SAVE_EVERY
        if len(times) % 20 == 1:
            print(f"t={t/60:6.1f} min  mean {mean_T[-1]:5.2f} C  top {top_T[-1]:5.2f}  bottom {bot_T[-1]:5.2f}  "
                  f"umax {umax_log[-1] if umax_log else 0:.4f} m/s  wall {time.time()-t0:5.0f}s", flush=True)
    # velocities
    u = np.zeros_like(psi); w = np.zeros_like(psi)
    u[1:-1, :] = (psi[2:, :] - psi[:-2, :]) / (2 * h)
    w[:, 1:-1] = -(psi[:, 2:] - psi[:, :-2]) / (2 * h)
    u[~fluid] = 0; w[~fluid] = 0
    umax = float(np.sqrt(u**2 + w**2).max())
    if step % 200 == 0: umax_log.append(umax)
    if umax * DT / h > 0.8: raise SystemExit(f"CFL too high ({umax*DT/h:.2f}) at t={t:.0f}s - reduce DT")
    # vorticity wall values (Thom)
    om_b = np.zeros_like(omega); cnt = np.zeros_like(omega)
    for dj, di in NB:
        nbr_fluid = np.roll(fluid, (-dj, -di), (0, 1))
        m = ~fluid & nbr_fluid
        np.add.at(om_b, np.nonzero(m), (-2 * np.roll(psi, (-dj, -di), (0, 1)) / h**2)[m]); cnt += m
    omega[~fluid] = np.where(cnt[~fluid] > 0, om_b[~fluid] / np.maximum(cnt[~fluid], 1), 0)
    # vorticity step
    Ta = T.copy(); Ta[sj, si] = T[src[:, 0], src[:, 1]]      # milk-side values on cartridge skin
    dTdx = np.zeros_like(T); dTdx[:, 1:-1] = (Ta[:, 2:] - Ta[:, :-2]) / (2 * h)
    rhs = omega + DT * (-upwind(omega, u, w) + G * BETA * dTdx)
    r = rhs[fluid]
    for rid, j2, i2 in bnd_pairs:
        np.add.at(r, rid, DT * NU / h**2 * omega[j2, i2])
    omega[fluid] = lu_w.solve(r)
    psi[fluid] = lu_psi.solve(-omega[fluid])
    # temperature step
    adv = upwind(Ta, u, w)
    rt = T[tnode] + DT * (-adv[tnode] + wall_src * (T_AMB - T[tnode]) + sink * T_ICE)
    T[tnode] = lu_T.solve(rt)
    t += DT; step += 1

np.savez_compressed("cfd_frames.npz", T=np.array(frames_T), psi=np.array(frames_psi), t=np.array(times),
                    mean=np.array(mean_T), top=np.array(top_T), bot=np.array(bot_T), obst=obst, x=x, z=z,
                    alpha=ALPHA, nu=NU, fscale=F_SCALE)
print(f"done: {step} steps in {time.time()-t0:.0f}s; saved cfd_frames.npz")
