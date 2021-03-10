import numpy as np
import copy


FDOH = 2
hc = [1.1382, - 0.046414]
nab = 2

"""
    Adjoint of the surface kernel. With the symmetrization strategy, we need to
    transform the adjoint kernel according to:
    
    F_s = S F
    
    where S is the surface kernel and F the seismic modeling kernel. The
    transformed operator is:
    
    F_s' = L S F
    
    where L and T are the transform matrices. Taking the adjoint:
    
    F_s'^* = ( L S L^-1 L F)^*
    
           = L F L^-1 S^* L
    knowing that  (L F) ^* = L F and that L^* = L et L^-1* = L^-1
     
    Performing the back transformation:
    
    L^-1 F_s'^* = F L^-1 S^* L
    
    To apply the free surface kernel, we must then apply the transformation
    L, then apply the free surface kernel S^* and do the back transformation.
    
    For the isotropic elastic wave equation, the transform matrices are:
    
   L = [rho   0
        0 -C^-1]
   L^-1 = [1/rho   0
           0   -C]
           
    where C is the rigidity tensor, given by:
    
    C [   M   M-2mu M-2mu 0   0   0
        M-2mu   M   M-2mu 0   0   0
        M-2mu M-2mu   M   0   0   0
          0     0     0   mu  0   0
          0     0     0   0   mu  0
          0     0     0   0   0   mu]
    
    C^-1 [ a [2M-2mu -M+2mu -M+2mu   0   0     0
             -M+2mu 2M-2mu -M+2mu    0   0     0
             -M+2mu -M+2mu 2M-2mu]   0   0     0
             0     0     0         1/mu  0     0
             0     0     0           0   1/mu  0
             0     0     0           0   0   1/mu]
             
    C^-1 [ a [M -M+2mu  0
             -M+2mu  M  0
               0     0  1/mu ]   in 2D
             
    a = 1/( 6Mmu - 4mu^2 )  in 3D
      
    a = 1/( 4Mmu - 4mu^2 )       in 2D
    
    In 2D, the transformation is thus:
    
    C^-1 sigma = [ a (M sxx - (M-2mu) szz),
                   a (M szz - (M-2mu) sxx),
                   1/mu sxy ]
"""


def Dpx(var):
    return hc[0] * (var[2:-2, 3:-1] - var[2:-2, 2:-2]) + hc[1] * (var[2:-2, 4:] - var[2:-2, 1:-3])


def Dmx(var):
    return hc[0] * (var[2:-2, 2:-2] - var[2:-2, 1:-3]) + hc[1] * (var[2:-2, 3:-1] - var[2:-2, 0:-4])


def Dpz(var):
    return hc[0] * (var[3:-1, 2:-2] - var[2:-2, 2:-2]) + hc[1] * (var[4:, 2:-2] - var[1:-3, 2:-2])


def Dmz(var):
    return hc[0] * (var[2:-2, 2:-2] - var[1:-3, 2:-2]) + hc[1] * (var[3:-1, 2:-2] - var[0:-4, 2:-2])


def taper(x, abpc=4.0, nab=2):

    a = -np.log(1.0-abpc/100)/nab**2
    return np.exp(a * x**2)


def cerjan(varin, abpc=4.0, nab=2):

    var = copy.copy(varin)
    h = np.expand_dims(taper(np.arange(nab)), axis=0)
    var[:, FDOH:FDOH+nab] *= h[::-1]
    var[:, -FDOH-nab:-FDOH] *= h
    var[-FDOH-nab:-FDOH, :] *= np.transpose(h)

    return var


def cv(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):

    vx = cerjan(vxi)
    vz = cerjan(vzi)

    return vx, vz, sxxi, szzi, sxzi


def cs(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):

    sxz = cerjan(sxzi)
    sxx = cerjan(sxxi)
    szz = cerjan(szzi)

    return vxi, vzi, sxx, szz, sxz


def apply_T(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):
    
    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)

    return vx, vz, -sxx, -szz, -sxz


def apply_L(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):

    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)
    
    a = 1.0 / (4.0 * M * mu - 4.0 * mu**2)
    vx[FDOH:-FDOH, FDOH:-FDOH] = vx[FDOH:-FDOH, FDOH:-FDOH] / rho
    vz[FDOH:-FDOH, FDOH:-FDOH] = vz[FDOH:-FDOH, FDOH:-FDOH] / rho
    sxx[FDOH:-FDOH, FDOH:-FDOH] = a *( M * sxxi[FDOH:-FDOH, FDOH:-FDOH] - (M-2.0*mu) * szzi[FDOH:-FDOH, FDOH:-FDOH])
    szz[FDOH:-FDOH, FDOH:-FDOH] = a *( M * szzi[FDOH:-FDOH, FDOH:-FDOH] - (M-2.0*mu) * sxxi[FDOH:-FDOH, FDOH:-FDOH])
    sxz[FDOH:-FDOH, FDOH:-FDOH] = sxzi[FDOH:-FDOH, FDOH:-FDOH] / mu



    return vx, vz, -sxx, -szz, -sxz


def apply_Lm(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):

    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)

    vx[FDOH:-FDOH, FDOH:-FDOH] = vx[FDOH:-FDOH, FDOH:-FDOH] * rho
    vz[FDOH:-FDOH, FDOH:-FDOH] = vz[FDOH:-FDOH, FDOH:-FDOH] * rho
    sxx[FDOH:-FDOH, FDOH:-FDOH] = M * sxxi[FDOH:-FDOH, FDOH:-FDOH] + (M-2.0*mu) * szzi[FDOH:-FDOH, FDOH:-FDOH]
    szz[FDOH:-FDOH, FDOH:-FDOH] = M * szzi[FDOH:-FDOH, FDOH:-FDOH] + (M-2.0*mu) * sxxi[FDOH:-FDOH, FDOH:-FDOH]
    sxz[FDOH:-FDOH, FDOH:-FDOH] = mu * sxzi[FDOH:-FDOH, FDOH:-FDOH]

    return vx, vz, -sxx, -szz, -sxz


def update_v(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):

    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)
    
    sxx_x = Dpx(sxx)
    szz_z = Dpz(szz)
    sxz_x = Dmx(sxz)
    sxz_z = Dmz(sxz)
    
    vx[FDOH:-FDOH, FDOH:-FDOH] += (sxx_x + sxz_z) * rho
    vz[FDOH:-FDOH, FDOH:-FDOH] += (szz_z + sxz_x) * rho

    return vx, vz, sxx, szz, sxz


def update_s(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):

    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)
    
    vx_x = Dmx(vx)
    vx_z = Dpz(vx)
    vz_x = Dpx(vz)
    vz_z = Dmz(vz)
    
    sxz[FDOH:-FDOH, FDOH:-FDOH] += mu * (vx_z + vz_x)
    sxx[FDOH:-FDOH, FDOH:-FDOH] += M * (vx_x + vz_z) - 2.0 * mu * vz_z
    szz[FDOH:-FDOH, FDOH:-FDOH] += M * (vx_x + vz_z) - 2.0 * mu * vx_x

    return vx, vz, sxx, szz, sxz


def surface(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):
    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)

    for ii in range(vx.shape[1] - 2*FDOH):
        szz[FDOH, ii+FDOH] = 0.0


        for jj in range(1,FDOH+1):
            szz[FDOH - jj, ii+FDOH] = -szz[FDOH+jj, ii+FDOH]
            sxz[FDOH - jj, ii+FDOH] = -sxz[FDOH+jj-1, ii+FDOH]

        vxx = 0
        vzz = 0
        for jj in range(FDOH):
            vxx += hc[jj] * (vx[FDOH, ii + FDOH + jj] - vx[FDOH, ii + FDOH - (jj + 1)])
            vzz += hc[jj] * (vz[FDOH + jj, ii + FDOH] - vz[FDOH - (jj + 1), ii + FDOH])

        f = mu[0, ii] * 2.0
        g = M[0, ii]
        h = -((g - f) * (g - f) * (vxx) / g) - ((g - f) * vzz)
        # if ii < nab:
        #     h *= taper(nab-ii)
        # elif ii >= vx.shape[1] - 2*FDOH - nab:
        #     h *= taper(ii, vx.shape[1] - 2*FDOH)

        sxx[FDOH, ii+FDOH] += h

    return vx, vz, sxx, szz, sxz


def surface_adj(vxi, vzi, sxxi, szzi, sxzi, rho, M, mu):
    vx = copy.copy(vxi)
    vz = copy.copy(vzi)
    sxx = copy.copy(sxxi)
    szz = copy.copy(szzi)
    sxz = copy.copy(sxzi)
    
    for ii in range(vx.shape[1] - 2*FDOH):
        szz[FDOH, ii+FDOH] = 0.0

        f = mu[0, ii] * 2.0
        g = M[0, ii]
        hx = -((g - f) * (g - f) / g)
        hz = -(g - f)
        # if ii < nab:
        #     hx *= taper(nab-ii)
        #     hz *= taper(nab-ii)
        # elif ii >= vx.shape[1] - 2*FDOH - nab:
        #     hx *= taper(ii, vx.shape[1] - 2*FDOH)
        #     hz *= taper(ii, vx.shape[1] - 2*FDOH)

#        for jj in range(1, FDOH+1):
#
#            szz[FDOH + jj, ii + FDOH] += -szz[FDOH - jj, ii + FDOH]
#            sxz[FDOH + jj - 1, ii + FDOH] += -sxz[FDOH - jj, ii + FDOH]
#            #szz[FDOH - jj, ii+FDOH] = 0
#            #sxz[FDOH - jj, ii+FDOH] = 0


        for jj in range(FDOH):
            if ii + jj < vx.shape[1] - 2*FDOH:
                vx[FDOH, ii + FDOH + jj] += hc[jj] * hx * sxx[FDOH, ii + FDOH]
            if ii + FDOH - (jj + 1) > FDOH-1:
                vx[FDOH, ii + FDOH - (jj + 1)] += - hc[jj] * hx * sxx[FDOH, ii + FDOH]

            vz[FDOH + jj, ii + FDOH] += hc[jj] * hz * sxx[FDOH, ii + FDOH]

    return vx, vz, sxx, szz, sxz




def dot_test(forwards, adjoints):

    vx = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vx[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    vz = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vz[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxx = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxx[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    szz = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    szz[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxz = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxz[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    Fvx = copy.copy(vx)
    Fvz = copy.copy(vz)
    Fsxx = copy.copy(sxx)
    Fszz = copy.copy(szz)
    Fsxz = copy.copy(sxz)

    vx_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vx_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    vz_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vz_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxx_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxx_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    szz_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    szz_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxz_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxz_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)

    Fvx_a = copy.copy(vx_a)
    Fvz_a = copy.copy(vz_a)
    Fsxx_a = copy.copy(sxx_a)
    Fszz_a = copy.copy(szz_a)
    Fsxz_a = copy.copy(sxz_a)

    for fun in forwards:
        (Fvx, Fvz, Fsxx, Fszz, Fsxz) = fun(Fvx, Fvz, Fsxx, Fszz, Fsxz,
                                           rho, M, mu)

    for fun in adjoints:
        (Fvx_a, Fvz_a, Fsxx_a, Fszz_a, Fsxz_a) = fun(Fvx_a, Fvz_a, Fsxx_a,
                                                     Fszz_a, Fsxz_a, rho, M, mu)

    prod1 = (  np.sum(vx_a*Fvx)
               + np.sum(vz_a*Fvz)
               + np.sum(sxx_a*Fsxx)
               + np.sum(szz_a*Fszz)
               + np.sum(sxz_a * Fsxz)
               )
    prod2 = (  np.sum(vx*Fvx_a)
               + np.sum(vz*Fvz_a)
               + np.sum(sxx*Fsxx_a)
               + np.sum(szz*Fszz_a)
               + np.sum(sxz * Fsxz_a)
               )

    return prod2-prod1


if __name__ == "__main__":
    
    
    vx = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vx[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    vz = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vz[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxx = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxx[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    szz = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    szz[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxz = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxz[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    
    vx_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vx_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    vz_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    vz_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxx_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxx_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    szz_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    szz_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    sxz_a = np.zeros([2 * FDOH + 10, 2 * FDOH + 10], np.float64)
    sxz_a[FDOH:-FDOH, FDOH:-FDOH] = np.random.rand(10, 10)
    
    
    M = np.float64(np.random.rand(10, 10))
    mu = np.float64(np.random.rand(10, 10))
    rho = np.float64(np.random.rand(10, 10))
    
    print("\nDot product for the surface kernel")
    print(dot_test([surface], [surface_adj]))


    print("\nDot product for the cerjan kernel")
    print(dot_test([cv, cs], [cv, cs]))


    print("\nTesting L is inverse of L^-1")
    (Fvx, Fvz, Fsxx, Fszz, Fsxz) = apply_L(vx, vz, sxx, szz, sxz, rho, M, mu)
    (Fvx, Fvz, Fsxx, Fszz, Fsxz) = apply_Lm(Fvx, Fvz, Fsxx, Fszz, Fsxz, rho, M, mu)
    diff = vx-Fvx + vz-Fvz + sxz-Fsxz + sxx-Fsxx + szz-Fszz
    print(np.max(diff))

    print("\nTesting T is inverse of T")
    (Fvx, Fvz, Fsxx, Fszz, Fsxz) = apply_T(vx, vz, sxx, szz, sxz, rho, M, mu)
    (Fvx, Fvz, Fsxx, Fszz, Fsxz) = apply_T(Fvx, Fvz, Fsxx, Fszz, Fsxz, rho, M, mu)
    diff = vx-Fvx + vz-Fvz + sxz-Fsxz + sxx-Fsxx + szz-Fszz
    print(np.max(diff))

    print("\nDot product for LFT")
    print(dot_test([update_v, update_s, apply_L],
                   [update_v, update_s, apply_L]))

    print("\nDot product for L U2 CV U1 ")
    print(dot_test([update_v, cv, update_s, apply_L],
                   [update_v, cv, update_s, apply_L]))

    print("\nDot product for F' = L CS US UV and F'^* =L US UV CS ")
    print(dot_test([update_v, update_s, cs, apply_L],
                   [cs, update_v, update_s, apply_L]))

    print("\nDot product for F_s' = LSF and F_s'^* = L F L^-1 S^* L  ")
    print(dot_test([update_v, update_s, surface, apply_L],
                   [apply_L, surface_adj, apply_Lm, update_v, update_s, apply_L]))


"""
Knowing that

    F = L US UV is self-adjoint
    
What is the adjoint of:

    F' = L CS US UV
    
    F'^* = UV^* US^* CS L
    
         = UV^* US^* L L^-1 CS L
         
         = (L US UV)^* L^-1 CS L
         
         = L US UV  L^-1 CS L
         
         = L US UV  L^-1 CS L (L and S commute)

Performing the back-transformation

    L^-1 F'^* = US UV CS

"""





