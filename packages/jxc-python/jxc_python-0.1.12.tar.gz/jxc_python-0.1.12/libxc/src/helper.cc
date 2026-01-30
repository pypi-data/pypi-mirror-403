#include <array>
#include <map>
#include <string>
#include <vector>
#include <cstddef>
#include "pybind11/numpy.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "visit_struct.hpp"


namespace py = pybind11;

extern "C" {
  struct xc_func_type;
}

typedef std::map<std::string, py::array> (*to_numpy)(xc_func_type*);
std::map<int, std::pair<std::string, to_numpy>> registry;

template <typename T>
decltype(auto) ToNumpy(const T& a) {
  using Scalar = typename std::remove_const<typename std::remove_reference<T>::type>::type;
  Scalar* data = new Scalar(static_cast<Scalar>(a));
  return py::array_t<Scalar>(std::array<int, 0>({}), data,
    py::capsule(data, [](void *f) {
      delete reinterpret_cast<Scalar*>(f);
    })
  );
}

template <typename T, size_t N>
decltype(auto) ToNumpy(const T (&a)[N]) {
  using Scalar = typename std::remove_const<T>::type;
  const Scalar* aa = reinterpret_cast<const Scalar*>(a);
  Scalar* data = new Scalar[N];
  std::memcpy(data, aa, N * sizeof(Scalar));
  return py::array_t<Scalar>(std::array<int, 1>({(int)N}), data,
    py::capsule(data, [](void *f) {
      delete[] reinterpret_cast<Scalar*>(f);
    })
  );
}

template <typename T, size_t N, size_t M>
decltype(auto) ToNumpy(const T (&a)[N][M]) {
  using Scalar = typename std::remove_const<T>::type;
  const Scalar* aa = reinterpret_cast<const Scalar*>(a);
  Scalar* data = new Scalar[N * M];
  std::memcpy(data, aa, N * M * sizeof(Scalar));
  return py::array_t<Scalar>(std::array<int, 2>({(int)N, (int)M}), data,
    py::capsule(data, [](void *f) {
      delete[] reinterpret_cast<Scalar*>(f);
    })
  );
}

#define REGISTER(STRUCT, ...)                                         \
  VISITABLE_STRUCT(STRUCT, __VA_ARGS__);                              \
  static auto STRUCT##_to_numpy(xc_func_type* func) {                 \
    std::map<std::string, py::array> ret;                             \
    visit_struct::for_each(*reinterpret_cast<STRUCT*>(func->params),  \
                           [&](const char* name, const auto& value) { \
                             ret[name] = ToNumpy(value);              \
                           });                                        \
    return ret;                                                       \
  }

static bool register_xc(const std::vector<int>& numbers,
                        const std::string& maple, to_numpy converter) {
  for (auto number : numbers) {
    registry[number] = std::make_pair(maple, converter);
  }
  return true;
}

// register all the structs

extern "C" {

// the xc_func_type struct from libxc

#include "xc.h"

// all param structs from libxc

typedef struct {
  double e1, c1, k0, b;
} mgga_x_mvsb_params;

typedef struct {
  double a;
} gga_k_lkt_params;

typedef struct {
  double gamma, at;
} mgga_x_br89_params;

typedef struct {
  double beta, gamma, a_c, omega;
} gga_c_pbe_erf_gws_params;

typedef struct {
  double a[12], d[6];
} mgga_x_m06l_params;

typedef struct {
  double beta, alpha, omega;
} gga_c_zvpbeint_params;

typedef struct {
  double beta, gamma, BB;
} gga_c_pbe_params;

typedef struct {
  double b, c, e, kappa, mu;
  double BLOC_a, BLOC_b;
} mgga_x_tpss_params;

typedef struct {
  double ltafrac;
} mgga_x_lta_params;

typedef struct {
  double gamma[2];
  double beta1[2];
  double beta2[2];
  double a[2], b[2], c[2], d[2];
} lda_c_pz_params;

typedef struct {
  double aa, bb, cc;
} gga_x_ol2_params;

typedef struct {
  double c_x[5], c_ss[5], c_ab[5];
} gga_xc_b97_params;

typedef struct {
  double gamma_ss, gamma_ab;
  const double css[5], cab[5];
  double Fermi_D_cnst;
} mgga_c_m05_params;

typedef struct {
  double a;
  double b;
  double c;
  double d;
  double m1;
  double m2;
  double omega;
} gga_c_lypr_params;

typedef struct {
  double kappa, alpha, muPBE, muGE;
} gga_k_apbeint_params;

typedef struct {
  double kappa, c, b, eta;
} mgga_x_msb86bl_params;

typedef struct {
  double mu[3];
} gga_k_lgap_ge_params;

typedef struct {
  double alpha;
  double beta;
  double gamma;
} gga_x_lb_params;

typedef struct {
  double beta, gamma;
  double c0, c1, c2;
} gga_x_hcth_a_params;

typedef struct {
  double T;
  double thetaParam;
  double b[2][5], c[2][3], d[2][5], e[2][5];
} lda_xc_ksdt_params;

typedef struct {
  double mu;
  double alpha;
} gga_k_vt84f_params;

typedef struct {
  double mu1;
  double kappa;
  double alpha;
  double beta;
  double gamma;
} gga_x_bkl_params;

typedef struct {
  double ap, bp, cp, af, bf, cf;
} lda_c_chachiyo_params;

typedef struct {
  double omega[19];
} gga_xc_th3_params;

typedef struct {
  double aa, bb, cc;
} gga_k_ol2_params;

typedef struct {
  double lm_f;
} gga_c_lm_params;

typedef struct {
  double alpha;
  double a1, a2, a3;
} lda_xc_1d_ehwlrg_params;

typedef struct {
  double ap, bp, cp, af, bf, cf;
} lda_c_chachiyo_mod_params;

typedef struct {
  double alphaoAx, c;
} gga_x_cap_params;

typedef struct {
  double fc, q;
} lda_c_ml1_params;

typedef struct {
  double a1, a2, a3, a4, a5, a6, a7, a8, a9, a10;
} gga_x_airy_params;

typedef struct {
  double c1;
  double c2;
  double c3;
  double c4;
  double c5;
} gga_c_ccdf_params;

typedef struct {
  double beta, alpha;
} gga_c_zpbeint_params;

typedef struct {
  double ct, at, bt, a2t, b2t, xt, cb, ab, bb, a2b, b2b, xb;
} mgga_x_ktbm_params;

typedef struct {
  double b, c, e, kappa, mu;
} mgga_x_rtpss_params;

typedef struct {
  double beta, gamma, BB;
} gga_c_pbe_vwn_params;

typedef struct {
  double a1, b1, alpha;
} gga_x_dk87_params;

typedef struct {
  double kappa, c, b;
} mgga_x_ms_params;

typedef struct {
  double N;
  double c;
} lda_c_2d_prm_params;

typedef struct {
  double css, copp;
} mgga_c_bc95_params;

typedef struct {
  double a, b, c, d, k;
} gga_c_wi_params;

typedef struct {
  double kappa;
  double mu[3];
} gga_k_lgap_params;

typedef struct {
  double c2, d, k1, eta;
} mgga_x_rppscan_params;

typedef struct {
  double ap, bp, cp, af, bf, cf, h;
} gga_c_chachiyo_params;

typedef struct {
  double c1, c2;
} gga_c_optc_params;

typedef struct {
  double c_x[5], c_ss[5], c_os[5];
} mgga_xc_b97mv_params;

typedef struct {
  double malpha;
  double mbeta;
  double mgamma;
  double mdelta;
  double aa;
  double bb;
  double ftilde;
} gga_c_p86vwn_params;

typedef struct {
  int k;
  int Nsp;
  double knots[14];
  double cx[10];
  double cc[10];
  double gammax;
  double gammac;
  double ax;
} hyb_gga_xc_case21_params;

typedef struct {
  double c_x[3], c_ss[5], c_os[5];
} hyb_mgga_xc_gas22_params;

typedef struct {
  double gamma_ss, gamma_ab, alpha_ss, alpha_ab;
  const double css[5], cab[5], dss[6], dab[6];
  double Fermi_D_cnst;
} mgga_c_m06l_params;

typedef struct {
  double B1, B2;
} gga_x_ak13_params;

typedef struct {
  const double m08_a[12], m08_b[12];
} mgga_c_m08_params;

typedef struct {
  double beta;
} lda_x_1d_soft_params;

typedef struct {
  double ltafrac;
} mgga_c_ltapw_params;

typedef struct {
  double hl_r[2], hl_c[2];
} lda_c_hl_params;

typedef struct {
  const double c[40];
} mgga_x_mn12_params;

typedef struct {
  double kappa, c, b;
} mgga_x_msb_params;

typedef struct {
  double a;
  double c1, c2, c3;
} gga_x_mpbe_params;

typedef struct {
  double a[6], b[9];
} gga_x_hjs_params;

typedef struct {
  double d;
  double C0_c[4];
} mgga_c_revtpss_params;

typedef struct {
  double c_x[5], c_ss[5], c_ab[5];
} hyb_gga_xc_wb97_params;

typedef struct {
  double a, b, c, d;
} gga_c_lyp_params;

typedef struct {
  double beta, gamma, omega;
} gga_x_b86_params;

typedef struct {
  double beta;
} lda_x_1d_exponential_params;

typedef struct {
  const double a[12];
  double csi_HF;
  double cx;
} hyb_mgga_x_m05_params;

typedef struct {
  double c1, c2, d, k1, eta;
  double dp2, dp4, da4;
} mgga_x_r4scan_params;

typedef struct {
  double a1, a2, a3;
  double b1, b2, b3;
} gga_x_ev93_params;

typedef struct {
  double a, AA, BB;
} mgga_x_gdme_params;

typedef struct {
  double kappa, c, b, eta;
} mgga_x_mspbel_params;

typedef struct {
  double eta;
} mgga_c_r2scan_params;

typedef struct {
  double rpbe_kappa, rpbe_mu;
} gga_x_rpbe_params;

typedef struct {
  double csk_a;
} mgga_k_csk_params;

typedef struct {
  double gamma;
  double css;
  double cab;
} mgga_c_b94_params;

typedef struct {
  double kappa, c, b, eta;
} mgga_x_msrpbel_params;

typedef struct {
  double A, B, C;
} lda_k_gds08_worker_params;

typedef struct {
  double gamma;
} mgga_x_br89_explicit_params;

typedef struct {
  double a, b;
} mgga_k_pc07_params;

typedef struct {
  double alpha, beta, mu, zeta;
} gga_x_ncap_params;

typedef struct {
  double alpha;
} lda_x_params;

typedef struct {
  double a, b, c;
} lda_c_epc17_params;

typedef struct {
  const double a[12], b[12];
} mgga_x_m08_params;

typedef struct {
  double e1, c1, k0, b;
} mgga_x_mvs_params;

typedef struct {
  double A, B, C, D, E;
  double bx;
} gga_x_s12_params;

typedef struct {
  double C1, C2, C3;
} lda_c_lp96_params;

typedef struct {
  double kappa;
  double mu;
  double alpha;
} gga_x_lsrpbe_params;

typedef struct {
  double kappa, mu;
  double lambda;
} gga_k_apbe_params;

typedef struct {
  double kappa, alpha, muPBE, muGE;
} gga_x_pbeint_params;

typedef struct {
  double alpha, c;
} gga_x_am05_params;

typedef struct {
  double pg_mu;
} gga_k_pg_params;

typedef struct {
  double beta, d;
  double C0_c[4];
} mgga_c_tpss_params;

typedef struct {
  double a, b, c;
} lda_c_epc18_params;

typedef struct {
  double eta;
} mgga_c_rppscan_params;

typedef struct {
  double a, b, gamma;
} gga_x_optx_params;

typedef struct {
  double a, b, c, d, f, alpha, expo;
} gga_x_pw91_params;

typedef struct {
  double kappa, mu;
  double lambda;
} gga_x_ityh_pbe_params;

typedef struct {
  double sogga11_a[6], sogga11_b[6];
} gga_c_sogga11_params;

typedef struct {
  double beta, gamma;
} gga_k_llp_params;

typedef struct {
  double task_c, task_d, task_h0x;
  double task_anu[3], task_bnu[5];
} mgga_x_task_params;

typedef struct {
  double c1, c2, d, k1;
  double eta, dp2;
} mgga_x_r2scan_params;

typedef struct {
  double A, B, C, D, E;
} gga_x_ssb_sw_params;

typedef struct {
  double cx_local[4];
  double cx_nlocal[4];
} mgga_x_tau_hcth_params;

typedef struct {
  double pp[3], a[3], alpha1[3];
  double beta1[3], beta2[3], beta3[3], beta4[3];
  double fz20;
} lda_c_pw_params;

typedef struct {
  double pgslb_mu, pgslb_beta;
} mgga_k_pgslb_params;

typedef struct {
  double beta0, beta1, beta2;
} gga_x_ft97_params;

typedef struct {
  double beta;
} gga_x_fd_lb94_params;

typedef struct {
  double kappa, mu, a[6], b[6];
} gga_x_sogga11_params;

typedef struct {
  double mu;
  double alpha;
} gga_x_vmt_params;

typedef struct {
  double kappa;
  double mu;
  double alpha;
} gga_x_lspbe_params;

typedef struct {
  double csk_a, csk_cp, csk_cq;
} mgga_k_csk_loc_params;

typedef struct {
  double a, b;
} lda_c_wigner_params;

typedef struct {
  double c2, d, k1;
  double taur, alphar;
} mgga_x_rscan_params;

typedef struct {
  double c0, c1, alphainf;
} mgga_x_gx_params;

typedef struct {
  double para[10], ferro[10];
  int interaction;
  double bb;
} lda_c_1d_csc_params;

typedef struct {
  double c_ss[5], c_ab[5];
} gga_c_bmk_params;

typedef struct {
  double c;
  double alpha;
} mgga_x_tb09_params;

typedef struct {
  double gamma, beta, lambda;
} mgga_x_mbr_params;

typedef struct {
  double mu;
  double alpha;
} gga_x_vmt84_params;

typedef struct {
  double kappa;
} mgga_k_lk_params;

typedef struct {
  double CC[4][4];
} gga_x_n12_params;

typedef struct {
  double kappa, mu;
  double lambda;
} gga_x_pbe_params;

typedef struct {
  double beta, gamma;
} gga_x_b88_params;

typedef struct {
  double a, b, gamma;
} gga_x_ityh_optx_params;

typedef struct {
  double a;
  double b;
  double a1;
  double a2;
  double b1;
  double b2;
} mgga_x_ft98_params;

typedef struct {
  double aa, bb, cc;
} gga_x_pw86_params;

typedef struct {
  double alpha, gamma;
} gga_c_am05_params;

typedef struct {
  double lambda, gamma;
} gga_k_tflw_params;

typedef struct {
  double c;
} mgga_c_ccalda_params;

typedef struct {
  double omega[21];
} gga_xc_th1_params;

typedef struct {
  double gamma, delta;
} gga_x_kt_params;

typedef struct {
  double A, B, C, D, E;
} hyb_gga_x_cam_s12_params;

typedef struct {
  double a;
  double b;
} lda_x_sloc_params;

typedef struct {
  double malpha;
  double mbeta;
  double mgamma;
  double mdelta;
  double aa;
  double bb;
  double ftilde;
} gga_c_p86_params;

typedef struct {
  double a;
  double c1, c2, c3;
} gga_k_mpbe_params;

typedef struct {
  const double alpha_ss, alpha_ab;
  const double dss[6], dab[6];
} mgga_c_vsxc_params;

typedef struct {
  double prefactor;
} mgga_x_rlda_params;

typedef struct {
  double ax;
} lda_k_tf_params;

typedef struct {
  double kappa, b_PBE, ax, omega;
} gga_x_pbe_erf_gws_params;

typedef struct {
  double c_x[3], c_ss[5], c_os[6];
} hyb_mgga_xc_wb97mv_params;

typedef struct {
  double a, b, c, d, f, alpha, expo;
} gga_k_lc94_params;

typedef struct {
  const double a[12], b[12], c[12], d[12];
} mgga_x_m11_l_params;

typedef struct {
  double A0, A1, A2, A3;
  double beta1, beta2, beta3;
  double a, b, c;
} mgga_k_rda_params;

typedef struct {
  double c, x0, a0;
} mgga_x_eel_params;

typedef struct {
  double a[6], b[9];
} gga_x_hjs_b88_v2_params;

typedef struct {
  double aa[5], bb[5];
} gga_k_dk_params;

typedef struct {
  const double a[12], b[12];
} mgga_x_m11_params;

typedef struct {
  double c1, c2, d, k1;
} mgga_x_scan_params;

typedef struct {
  double C2;
  double p;
} gga_k_rational_p_params;

typedef struct {
  double beta;
  double gamma;
} mgga_x_jk_params;


}

// use visit struct to convert param struct to python

std::vector<int> gga_c_tca_numbers = {
  100
};
bool gga_c_tca_registered = register_xc(
  gga_c_tca_numbers, "gga_c_tca", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_2d_b88_numbers = {
  127
};
bool gga_x_2d_b88_registered = register_xc(
  gga_x_2d_b88_numbers, "gga_x_2d_b88", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mvsb_numbers = {
  302, 303
};
REGISTER(mgga_x_mvsb_params, e1, c1, k0, b);
bool mgga_x_mvsb_registered = register_xc(
  mgga_x_mvsb_numbers, "mgga_x_mvsb", mgga_x_mvsb_params_to_numpy
);
std::vector<int> gga_k_lkt_numbers = {
  613
};
REGISTER(gga_k_lkt_params, a);
bool gga_k_lkt_registered = register_xc(
  gga_k_lkt_numbers, "gga_k_lkt", gga_k_lkt_params_to_numpy
);
std::vector<int> gga_c_op_xalpha_numbers = {
  84
};
bool gga_c_op_xalpha_registered = register_xc(
  gga_c_op_xalpha_numbers, "gga_c_op_xalpha", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_acggap_numbers = {
  176
};
bool gga_c_acggap_registered = register_xc(
  gga_c_acggap_numbers, "gga_c_acggap", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_htbs_numbers = {
  191
};
bool gga_x_htbs_registered = register_xc(
  gga_x_htbs_numbers, "gga_x_htbs", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_pbea_numbers = {
  121
};
bool gga_x_pbea_registered = register_xc(
  gga_x_pbea_numbers, "gga_x_pbea", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_x_erf_numbers = {
  546, 653
};
bool lda_x_erf_registered = register_xc(
  lda_x_erf_numbers, "lda_x_erf", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_br89_numbers = {
  206, 214, 284
};
REGISTER(mgga_x_br89_params, gamma, at);
bool mgga_x_br89_registered = register_xc(
  mgga_x_br89_numbers, "mgga_x_br89", mgga_x_br89_params_to_numpy
);
std::vector<int> gga_c_pbe_erf_gws_numbers = {
  657
};
REGISTER(gga_c_pbe_erf_gws_params, beta, gamma, a_c, omega);
bool gga_c_pbe_erf_gws_registered = register_xc(
  gga_c_pbe_erf_gws_numbers, "gga_c_pbe_erf_gws", gga_c_pbe_erf_gws_params_to_numpy
);
std::vector<int> lda_k_zlp_numbers = {
  550
};
bool lda_k_zlp_registered = register_xc(
  lda_k_zlp_numbers, "lda_k_zlp", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_m06l_numbers = {
  203, 444, 449, 293, 305, 310
};
REGISTER(mgga_x_m06l_params, a, d);
bool mgga_x_m06l_registered = register_xc(
  mgga_x_m06l_numbers, "mgga_x_m06l", mgga_x_m06l_params_to_numpy
);
std::vector<int> gga_c_zvpbeint_numbers = {
  557, 558
};
REGISTER(gga_c_zvpbeint_params, beta, alpha, omega);
bool gga_c_zvpbeint_registered = register_xc(
  gga_c_zvpbeint_numbers, "gga_c_zvpbeint", gga_c_zvpbeint_params_to_numpy
);
std::vector<int> gga_c_revtca_numbers = {
  99
};
bool gga_c_revtca_registered = register_xc(
  gga_c_revtca_numbers, "gga_c_revtca", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_pbe_numbers = {
  130, 133, 322, 136, 138, 143, 186, 89, 62, 258, 272, 560, 712
};
REGISTER(gga_c_pbe_params, beta, gamma, BB);
bool gga_c_pbe_registered = register_xc(
  gga_c_pbe_numbers, "gga_c_pbe", gga_c_pbe_params_to_numpy
);
std::vector<int> mgga_x_tpss_numbers = {
  202, 245, 212, 244
};
REGISTER(mgga_x_tpss_params, b, c, e, kappa, mu, BLOC_a, BLOC_b);
bool mgga_x_tpss_registered = register_xc(
  mgga_x_tpss_numbers, "mgga_x_tpss", mgga_x_tpss_params_to_numpy
);
std::vector<int> mgga_x_lta_numbers = {
  201, 685, 698
};
REGISTER(mgga_x_lta_params, ltafrac);
bool mgga_x_lta_registered = register_xc(
  mgga_x_lta_numbers, "mgga_x_lta", mgga_x_lta_params_to_numpy
);
std::vector<int> lda_c_pz_numbers = {
  9, 10, 11
};
REGISTER(lda_c_pz_params, gamma, beta1, beta2, a, b, c, d);
bool lda_c_pz_registered = register_xc(
  lda_c_pz_numbers, "lda_c_pz", lda_c_pz_params_to_numpy
);
std::vector<int> gga_x_ol2_numbers = {
  183
};
REGISTER(gga_x_ol2_params, aa, bb, cc);
bool gga_x_ol2_registered = register_xc(
  gga_x_ol2_numbers, "gga_x_ol2", gga_x_ol2_params_to_numpy
);
std::vector<int> gga_xc_b97_numbers = {
  407, 408, 410, 170, 327, 413, 414, 161, 162, 163, 164, 420, 421, 422, 423, 424, 425, 96, 95, 94, 93, 266, 545
};
REGISTER(gga_xc_b97_params, c_x, c_ss, c_ab);
bool gga_xc_b97_registered = register_xc(
  gga_xc_b97_numbers, "gga_xc_b97", gga_xc_b97_params_to_numpy
);
std::vector<int> mgga_xc_zlp_numbers = {
  42
};
bool mgga_xc_zlp_registered = register_xc(
  mgga_xc_zlp_numbers, "mgga_xc_zlp", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_m05_numbers = {
  237, 238, 37
};
REGISTER(mgga_c_m05_params, gamma_ss, gamma_ab, css, cab, Fermi_D_cnst);
bool mgga_c_m05_registered = register_xc(
  mgga_c_m05_numbers, "mgga_c_m05", mgga_c_m05_params_to_numpy
);
std::vector<int> gga_x_q2d_numbers = {
  48
};
bool gga_x_q2d_registered = register_xc(
  gga_x_q2d_numbers, "gga_x_q2d", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_lypr_numbers = {
  624
};
REGISTER(gga_c_lypr_params, a, b, c, d, m1, m2, omega);
bool gga_c_lypr_registered = register_xc(
  gga_c_lypr_numbers, "gga_c_lypr", gga_c_lypr_params_to_numpy
);
std::vector<int> gga_k_apbeint_numbers = {
  54, 53
};
REGISTER(gga_k_apbeint_params, kappa, alpha, muPBE, muGE);
bool gga_k_apbeint_registered = register_xc(
  gga_k_apbeint_numbers, "gga_k_apbeint", gga_k_apbeint_params_to_numpy
);
std::vector<int> mgga_x_msb86bl_numbers = {
  765, 766
};
REGISTER(mgga_x_msb86bl_params, kappa, c, b, eta);
bool mgga_x_msb86bl_registered = register_xc(
  mgga_x_msb86bl_numbers, "mgga_x_msb86bl", mgga_x_msb86bl_params_to_numpy
);
std::vector<int> gga_k_lgap_ge_numbers = {
  633
};
REGISTER(gga_k_lgap_ge_params, mu);
bool gga_k_lgap_ge_registered = register_xc(
  gga_k_lgap_ge_numbers, "gga_k_lgap_ge", gga_k_lgap_ge_params_to_numpy
);
std::vector<int> gga_x_lb_numbers = {
  160, 182
};
REGISTER(gga_x_lb_params, alpha, beta, gamma);
bool gga_x_lb_registered = register_xc(
  gga_x_lb_numbers, "gga_x_lb", gga_x_lb_params_to_numpy
);
std::vector<int> mgga_c_scan_numbers = {
  267, 292, 584
};
bool mgga_c_scan_registered = register_xc(
  mgga_c_scan_numbers, "mgga_c_scan", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_hcth_a_numbers = {
  34
};
REGISTER(gga_x_hcth_a_params, beta, gamma, c0, c1, c2);
bool gga_x_hcth_a_registered = register_xc(
  gga_x_hcth_a_numbers, "gga_x_hcth_a", gga_x_hcth_a_params_to_numpy
);
std::vector<int> lda_c_gombas_numbers = {
  24
};
bool lda_c_gombas_registered = register_xc(
  lda_c_gombas_numbers, "lda_c_gombas", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_mgga_x_dldf_numbers = {
  36
};
bool hyb_mgga_x_dldf_registered = register_xc(
  hyb_mgga_x_dldf_numbers, "hyb_mgga_x_dldf", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_xc_ksdt_numbers = {
  259, 577, 318
};
REGISTER(lda_xc_ksdt_params, T, thetaParam, b, c, d, e);
bool lda_xc_ksdt_registered = register_xc(
  lda_xc_ksdt_numbers, "lda_xc_ksdt", lda_xc_ksdt_params_to_numpy
);
std::vector<int> gga_k_vt84f_numbers = {
  619
};
REGISTER(gga_k_vt84f_params, mu, alpha);
bool gga_k_vt84f_registered = register_xc(
  gga_k_vt84f_numbers, "gga_k_vt84f", gga_k_vt84f_params_to_numpy
);
std::vector<int> gga_x_bkl_numbers = {
  338, 339
};
REGISTER(gga_x_bkl_params, mu1, kappa, alpha, beta, gamma);
bool gga_x_bkl_registered = register_xc(
  gga_x_bkl_numbers, "gga_x_bkl", gga_x_bkl_params_to_numpy
);
std::vector<int> lda_c_chachiyo_numbers = {
  287, 579
};
REGISTER(lda_c_chachiyo_params, ap, bp, cp, af, bf, cf);
bool lda_c_chachiyo_registered = register_xc(
  lda_c_chachiyo_numbers, "lda_c_chachiyo", lda_c_chachiyo_params_to_numpy
);
std::vector<int> gga_xc_th3_numbers = {
  156, 157
};
REGISTER(gga_xc_th3_params, omega);
bool gga_xc_th3_registered = register_xc(
  gga_xc_th3_numbers, "gga_xc_th3", gga_xc_th3_params_to_numpy
);
std::vector<int> gga_k_ol2_numbers = {
  513
};
REGISTER(gga_k_ol2_params, aa, bb, cc);
bool gga_k_ol2_registered = register_xc(
  gga_k_ol2_numbers, "gga_k_ol2", gga_k_ol2_params_to_numpy
);
std::vector<int> gga_c_pbeloc_numbers = {
  246
};
bool gga_c_pbeloc_registered = register_xc(
  gga_c_pbeloc_numbers, "gga_c_pbeloc", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mcml_numbers = {
  644
};
bool mgga_x_mcml_registered = register_xc(
  mgga_x_mcml_numbers, "mgga_x_mcml", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_cc_numbers = {
  387
};
bool mgga_c_cc_registered = register_xc(
  mgga_c_cc_numbers, "mgga_c_cc", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_hcth_a_numbers = {
  97
};
bool gga_c_hcth_a_registered = register_xc(
  gga_c_hcth_a_numbers, "gga_c_hcth_a", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_pkzb_numbers = {
  213
};
bool mgga_x_pkzb_registered = register_xc(
  mgga_x_pkzb_numbers, "mgga_x_pkzb", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_lm_numbers = {
  137
};
REGISTER(gga_c_lm_params, lm_f);
bool gga_c_lm_registered = register_xc(
  gga_c_lm_numbers, "gga_c_lm", gga_c_lm_params_to_numpy
);
std::vector<int> gga_x_c09x_numbers = {
  158
};
bool gga_x_c09x_registered = register_xc(
  gga_x_c09x_numbers, "gga_x_c09x", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_xc_1d_ehwlrg_numbers = {
  536, 537, 538
};
REGISTER(lda_xc_1d_ehwlrg_params, alpha, a1, a2, a3);
bool lda_xc_1d_ehwlrg_registered = register_xc(
  lda_xc_1d_ehwlrg_numbers, "lda_xc_1d_ehwlrg", lda_xc_1d_ehwlrg_params_to_numpy
);
std::vector<int> lda_c_chachiyo_mod_numbers = {
  307, 308
};
REGISTER(lda_c_chachiyo_mod_params, ap, bp, cp, af, bf, cf);
bool lda_c_chachiyo_mod_registered = register_xc(
  lda_c_chachiyo_mod_numbers, "lda_c_chachiyo_mod", lda_c_chachiyo_mod_params_to_numpy
);
std::vector<int> gga_x_cap_numbers = {
  270, 477
};
REGISTER(gga_x_cap_params, alphaoAx, c);
bool gga_x_cap_registered = register_xc(
  gga_x_cap_numbers, "gga_x_cap", gga_x_cap_params_to_numpy
);
std::vector<int> lda_c_ml1_numbers = {
  22, 23
};
REGISTER(lda_c_ml1_params, fc, q);
bool lda_c_ml1_registered = register_xc(
  lda_c_ml1_numbers, "lda_c_ml1", lda_c_ml1_params_to_numpy
);
std::vector<int> gga_x_airy_numbers = {
  192, 193
};
REGISTER(gga_x_airy_params, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10);
bool gga_x_airy_registered = register_xc(
  gga_x_airy_numbers, "gga_x_airy", gga_x_airy_params_to_numpy
);
std::vector<int> gga_c_ccdf_numbers = {
  313
};
REGISTER(gga_c_ccdf_params, c1, c2, c3, c4, c5);
bool gga_c_ccdf_registered = register_xc(
  gga_c_ccdf_numbers, "gga_c_ccdf", gga_c_ccdf_params_to_numpy
);
std::vector<int> gga_c_zpbeint_numbers = {
  61, 63
};
REGISTER(gga_c_zpbeint_params, beta, alpha);
bool gga_c_zpbeint_registered = register_xc(
  gga_c_zpbeint_numbers, "gga_c_zpbeint", gga_c_zpbeint_params_to_numpy
);
std::vector<int> mgga_x_ktbm_numbers = {
  735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760
};
REGISTER(mgga_x_ktbm_params, ct, at, bt, a2t, b2t, xt, cb, ab, bb, a2b, b2b, xb);
bool mgga_x_ktbm_registered = register_xc(
  mgga_x_ktbm_numbers, "mgga_x_ktbm", mgga_x_ktbm_params_to_numpy
);
std::vector<int> mgga_x_revtm_numbers = {
  693
};
bool mgga_x_revtm_registered = register_xc(
  mgga_x_revtm_numbers, "mgga_x_revtm", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_c_vwn_1_numbers = {
  28
};
bool lda_c_vwn_1_registered = register_xc(
  lda_c_vwn_1_numbers, "lda_c_vwn_1", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mbeef_numbers = {
  249
};
bool mgga_x_mbeef_registered = register_xc(
  mgga_x_mbeef_numbers, "mgga_x_mbeef", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_rtpss_numbers = {
  299
};
REGISTER(mgga_x_rtpss_params, b, c, e, kappa, mu);
bool mgga_x_rtpss_registered = register_xc(
  mgga_x_rtpss_numbers, "mgga_x_rtpss", mgga_x_rtpss_params_to_numpy
);
std::vector<int> gga_c_pbe_vwn_numbers = {
  216
};
REGISTER(gga_c_pbe_vwn_params, beta, gamma, BB);
bool gga_c_pbe_vwn_registered = register_xc(
  gga_c_pbe_vwn_numbers, "gga_c_pbe_vwn", gga_c_pbe_vwn_params_to_numpy
);
std::vector<int> gga_x_gg99_numbers = {
  535, 544
};
bool gga_x_gg99_registered = register_xc(
  gga_x_gg99_numbers, "gga_x_gg99", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_op_b88_numbers = {
  87
};
bool gga_c_op_b88_registered = register_xc(
  gga_c_op_b88_numbers, "gga_c_op_b88", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_dk87_numbers = {
  111, 112
};
REGISTER(gga_x_dk87_params, a1, b1, alpha);
bool gga_x_dk87_registered = register_xc(
  gga_x_dk87_numbers, "gga_x_dk87", gga_x_dk87_params_to_numpy
);
std::vector<int> lda_c_rpa_numbers = {
  3
};
bool lda_c_rpa_registered = register_xc(
  lda_c_rpa_numbers, "lda_c_rpa", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_ms_numbers = {
  221, 222, 223, 224, 228
};
REGISTER(mgga_x_ms_params, kappa, c, b);
bool mgga_x_ms_registered = register_xc(
  mgga_x_ms_numbers, "mgga_x_ms", mgga_x_ms_params_to_numpy
);
std::vector<int> lda_c_2d_prm_numbers = {
  16
};
REGISTER(lda_c_2d_prm_params, N, c);
bool lda_c_2d_prm_registered = register_xc(
  lda_c_2d_prm_numbers, "lda_c_2d_prm", lda_c_2d_prm_params_to_numpy
);
std::vector<int> mgga_c_bc95_numbers = {
  240
};
REGISTER(mgga_c_bc95_params, css, copp);
bool mgga_c_bc95_registered = register_xc(
  mgga_c_bc95_numbers, "mgga_c_bc95", mgga_c_bc95_params_to_numpy
);
std::vector<int> gga_c_wi_numbers = {
  153, 148
};
REGISTER(gga_c_wi_params, a, b, c, d, k);
bool gga_c_wi_registered = register_xc(
  gga_c_wi_numbers, "gga_c_wi", gga_c_wi_params_to_numpy
);
std::vector<int> lda_x_rel_numbers = {
  532
};
bool lda_x_rel_registered = register_xc(
  lda_x_rel_numbers, "lda_x_rel", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_xc_cc06_numbers = {
  229
};
bool mgga_xc_cc06_registered = register_xc(
  mgga_xc_cc06_numbers, "mgga_xc_cc06", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_beefvdw_numbers = {
  285, 286
};
bool gga_x_beefvdw_registered = register_xc(
  gga_x_beefvdw_numbers, "gga_x_beefvdw", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_lgap_numbers = {
  620
};
REGISTER(gga_k_lgap_params, kappa, mu);
bool gga_k_lgap_registered = register_xc(
  gga_k_lgap_numbers, "gga_k_lgap", gga_k_lgap_params_to_numpy
);
std::vector<int> mgga_c_kcisk_numbers = {
  638
};
bool mgga_c_kcisk_registered = register_xc(
  mgga_c_kcisk_numbers, "mgga_c_kcisk", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_meyer_numbers = {
  57
};
bool gga_k_meyer_registered = register_xc(
  gga_k_meyer_numbers, "gga_k_meyer", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_rppscan_numbers = {
  648
};
REGISTER(mgga_x_rppscan_params, c2, d, k1, eta);
bool mgga_x_rppscan_registered = register_xc(
  mgga_x_rppscan_numbers, "mgga_x_rppscan", mgga_x_rppscan_params_to_numpy
);
std::vector<int> gga_c_chachiyo_numbers = {
  309
};
REGISTER(gga_c_chachiyo_params, ap, bp, cp, af, bf, cf, h);
bool gga_c_chachiyo_registered = register_xc(
  gga_c_chachiyo_numbers, "gga_c_chachiyo", gga_c_chachiyo_params_to_numpy
);
std::vector<int> gga_x_sg4_numbers = {
  533
};
bool gga_x_sg4_registered = register_xc(
  gga_x_sg4_numbers, "gga_x_sg4", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_optc_numbers = {
  200
};
REGISTER(gga_c_optc_params, c1, c2);
bool gga_c_optc_registered = register_xc(
  gga_c_optc_numbers, "gga_c_optc", gga_c_optc_params_to_numpy
);
std::vector<int> mgga_xc_b97mv_numbers = {
  254
};
REGISTER(mgga_xc_b97mv_params, c_x, c_ss, c_os);
bool mgga_xc_b97mv_registered = register_xc(
  mgga_xc_b97mv_numbers, "mgga_xc_b97mv", mgga_xc_b97mv_params_to_numpy
);
std::vector<int> gga_x_ityh_numbers = {
  529
};
bool gga_x_ityh_registered = register_xc(
  gga_x_ityh_numbers, "gga_x_ityh", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_op_pw91_numbers = {
  262
};
bool gga_c_op_pw91_registered = register_xc(
  gga_c_op_pw91_numbers, "gga_c_op_pw91", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_rge2_numbers = {
  142
};
bool gga_x_rge2_registered = register_xc(
  gga_x_rge2_numbers, "gga_x_rge2", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_p86vwn_numbers = {
  252, 253
};
REGISTER(gga_c_p86vwn_params, malpha, mbeta, mgamma, mdelta, aa, bb, ftilde);
bool gga_c_p86vwn_registered = register_xc(
  gga_c_p86vwn_numbers, "gga_c_p86vwn", gga_c_p86vwn_params_to_numpy
);
std::vector<int> lda_c_2d_amgb_numbers = {
  15
};
bool lda_c_2d_amgb_registered = register_xc(
  lda_c_2d_amgb_numbers, "lda_c_2d_amgb", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_gga_xc_case21_numbers = {
  390
};
REGISTER(hyb_gga_xc_case21_params, k, Nsp, knots, cx, cc, gammax, gammac, ax);
bool hyb_gga_xc_case21_registered = register_xc(
  hyb_gga_xc_case21_numbers, "hyb_gga_xc_case21", hyb_gga_xc_case21_params_to_numpy
);
std::vector<int> gga_x_2d_b86_numbers = {
  128
};
bool gga_x_2d_b86_registered = register_xc(
  gga_x_2d_b86_numbers, "gga_x_2d_b86", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_mgga_xc_gas22_numbers = {
  658
};
REGISTER(hyb_mgga_xc_gas22_params, c_x, c_ss, c_os);
bool hyb_mgga_xc_gas22_registered = register_xc(
  hyb_mgga_xc_gas22_numbers, "hyb_mgga_xc_gas22", hyb_mgga_xc_gas22_params_to_numpy
);
std::vector<int> mgga_c_m06l_numbers = {
  233, 234, 235, 236, 294, 306, 311
};
REGISTER(mgga_c_m06l_params, gamma_ss, gamma_ab, alpha_ss, alpha_ab, css, cab, dss, dab, Fermi_D_cnst);
bool mgga_c_m06l_registered = register_xc(
  mgga_c_m06l_numbers, "mgga_c_m06l", mgga_c_m06l_params_to_numpy
);
std::vector<int> gga_c_op_pbe_numbers = {
  86
};
bool gga_c_op_pbe_registered = register_xc(
  gga_c_op_pbe_numbers, "gga_c_op_pbe", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_ak13_numbers = {
  56
};
REGISTER(gga_x_ak13_params, B1, B2);
bool gga_x_ak13_registered = register_xc(
  gga_x_ak13_numbers, "gga_x_ak13", gga_x_ak13_params_to_numpy
);
std::vector<int> gga_c_wl_numbers = {
  147
};
bool gga_c_wl_registered = register_xc(
  gga_c_wl_numbers, "gga_c_wl", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_m08_numbers = {
  78, 77, 76, 75, 74, 73, 261, 269, 172, 341
};
REGISTER(mgga_c_m08_params, m08_a, m08_b);
bool mgga_c_m08_registered = register_xc(
  mgga_c_m08_numbers, "mgga_c_m08", mgga_c_m08_params_to_numpy
);
std::vector<int> lda_x_1d_soft_numbers = {
  21
};
REGISTER(lda_x_1d_soft_params, beta);
bool lda_x_1d_soft_registered = register_xc(
  lda_x_1d_soft_numbers, "lda_x_1d_soft", lda_x_1d_soft_params_to_numpy
);
std::vector<int> mgga_c_ltapw_numbers = {
  699
};
REGISTER(mgga_c_ltapw_params, ltafrac);
bool mgga_c_ltapw_registered = register_xc(
  mgga_c_ltapw_numbers, "mgga_c_ltapw", mgga_c_ltapw_params_to_numpy
);
std::vector<int> gga_x_g96_numbers = {
  107
};
bool gga_x_g96_registered = register_xc(
  gga_x_g96_numbers, "gga_x_g96", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_kcis_numbers = {
  562, 563
};
bool mgga_c_kcis_registered = register_xc(
  mgga_c_kcis_numbers, "mgga_c_kcis", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_c_hl_numbers = {
  4, 5, 17
};
REGISTER(lda_c_hl_params, hl_r, hl_c);
bool lda_c_hl_registered = register_xc(
  lda_c_hl_numbers, "lda_c_hl", lda_c_hl_params_to_numpy
);
std::vector<int> mgga_x_mn12_numbers = {
  227, 248, 260, 268, 340
};
REGISTER(mgga_x_mn12_params, c);
bool mgga_x_mn12_registered = register_xc(
  mgga_x_mn12_numbers, "mgga_x_mn12", mgga_x_mn12_params_to_numpy
);
std::vector<int> lda_xc_tih_numbers = {
  599
};
bool lda_xc_tih_registered = register_xc(
  lda_xc_tih_numbers, "lda_xc_tih", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_pbepow_numbers = {
  539
};
bool gga_x_pbepow_registered = register_xc(
  gga_x_pbepow_numbers, "gga_x_pbepow", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_msb_numbers = {
  300, 301
};
REGISTER(mgga_x_msb_params, kappa, c, b);
bool mgga_x_msb_registered = register_xc(
  mgga_x_msb_numbers, "mgga_x_msb", mgga_x_msb_params_to_numpy
);
std::vector<int> mgga_x_vt84_numbers = {
  541
};
bool mgga_x_vt84_registered = register_xc(
  mgga_x_vt84_numbers, "mgga_x_vt84", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_pbetrans_numbers = {
  291
};
bool gga_x_pbetrans_registered = register_xc(
  gga_x_pbetrans_numbers, "gga_x_pbetrans", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_mpbe_numbers = {
  122
};
REGISTER(gga_x_mpbe_params, a, c1, c2, c3);
bool gga_x_mpbe_registered = register_xc(
  gga_x_mpbe_numbers, "gga_x_mpbe", gga_x_mpbe_params_to_numpy
);
std::vector<int> gga_x_hjs_numbers = {
  525, 526, 527, 528
};
REGISTER(gga_x_hjs_params, a, b);
bool gga_x_hjs_registered = register_xc(
  gga_x_hjs_numbers, "gga_x_hjs", gga_x_hjs_params_to_numpy
);
std::vector<int> mgga_c_revtpss_numbers = {
  241, 694
};
REGISTER(mgga_c_revtpss_params, d, C0_c);
bool mgga_c_revtpss_registered = register_xc(
  mgga_c_revtpss_numbers, "mgga_c_revtpss", mgga_c_revtpss_params_to_numpy
);
std::vector<int> gga_c_acgga_numbers = {
  39
};
bool gga_c_acgga_registered = register_xc(
  gga_c_acgga_numbers, "gga_c_acgga", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_gga_xc_wb97_numbers = {
  463, 464, 466, 471, 399
};
REGISTER(hyb_gga_xc_wb97_params, c_x, c_ss, c_ab);
bool hyb_gga_xc_wb97_registered = register_xc(
  hyb_gga_xc_wb97_numbers, "hyb_gga_xc_wb97", hyb_gga_xc_wb97_params_to_numpy
);
std::vector<int> gga_x_lg93_numbers = {
  113
};
bool gga_x_lg93_registered = register_xc(
  gga_x_lg93_numbers, "gga_x_lg93", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_regtm_numbers = {
  626
};
bool mgga_x_regtm_registered = register_xc(
  mgga_x_regtm_numbers, "mgga_x_regtm", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_b88_numbers = {
  571
};
bool mgga_c_b88_registered = register_xc(
  mgga_c_b88_numbers, "mgga_c_b88", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_lyp_numbers = {
  131, 559, 314
};
REGISTER(gga_c_lyp_params, a, b, c, d);
bool gga_c_lyp_registered = register_xc(
  gga_c_lyp_numbers, "gga_c_lyp", gga_c_lyp_params_to_numpy
);
std::vector<int> gga_x_b86_numbers = {
  103, 105, 41, 171
};
REGISTER(gga_x_b86_params, beta, gamma, omega);
bool gga_x_b86_registered = register_xc(
  gga_x_b86_numbers, "gga_x_b86", gga_x_b86_params_to_numpy
);
std::vector<int> lda_x_1d_exponential_numbers = {
  600
};
REGISTER(lda_x_1d_exponential_params, beta);
bool lda_x_1d_exponential_registered = register_xc(
  lda_x_1d_exponential_numbers, "lda_x_1d_exponential", lda_x_1d_exponential_params_to_numpy
);
std::vector<int> lda_x_yukawa_numbers = {
  641
};
bool lda_x_yukawa_registered = register_xc(
  lda_x_yukawa_numbers, "lda_x_yukawa", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_mgga_x_m05_numbers = {
  438, 439, 450
};
REGISTER(hyb_mgga_x_m05_params, a, csi_HF, cx);
bool hyb_mgga_x_m05_registered = register_xc(
  hyb_mgga_x_m05_numbers, "hyb_mgga_x_m05", hyb_mgga_x_m05_params_to_numpy
);
std::vector<int> lda_c_rc04_numbers = {
  27
};
bool lda_c_rc04_registered = register_xc(
  lda_c_rc04_numbers, "lda_c_rc04", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_xc_lp90_numbers = {
  564
};
bool mgga_xc_lp90_registered = register_xc(
  mgga_xc_lp90_numbers, "mgga_xc_lp90", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_r4scan_numbers = {
  650
};
REGISTER(mgga_x_r4scan_params, c1, c2, d, k1, eta, dp2, dp4, da4);
bool mgga_x_r4scan_registered = register_xc(
  mgga_x_r4scan_numbers, "mgga_x_r4scan", mgga_x_r4scan_params_to_numpy
);
std::vector<int> gga_x_ev93_numbers = {
  35, 215
};
REGISTER(gga_x_ev93_params, a1, a2, a3, b1, b2, b3);
bool gga_x_ev93_registered = register_xc(
  gga_x_ev93_numbers, "gga_x_ev93", gga_x_ev93_params_to_numpy
);
std::vector<int> mgga_k_gea2_numbers = {
  627
};
bool mgga_k_gea2_registered = register_xc(
  mgga_k_gea2_numbers, "mgga_k_gea2", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_2d_b86_mgc_numbers = {
  124
};
bool gga_x_2d_b86_mgc_registered = register_xc(
  gga_x_2d_b86_mgc_numbers, "gga_x_2d_b86_mgc", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_ft97_numbers = {
  88
};
bool gga_c_ft97_registered = register_xc(
  gga_c_ft97_numbers, "gga_c_ft97", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_gdme_numbers = {
  687, 689, 690, 691
};
REGISTER(mgga_x_gdme_params, a, AA, BB);
bool mgga_x_gdme_registered = register_xc(
  mgga_x_gdme_numbers, "mgga_x_gdme", mgga_x_gdme_params_to_numpy
);
std::vector<int> mgga_k_gea4_numbers = {
  628
};
bool mgga_k_gea4_registered = register_xc(
  mgga_k_gea4_numbers, "mgga_k_gea4", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_rregtm_numbers = {
  391
};
bool mgga_c_rregtm_registered = register_xc(
  mgga_c_rregtm_numbers, "mgga_c_rregtm", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mspbel_numbers = {
  761, 762
};
REGISTER(mgga_x_mspbel_params, kappa, c, b, eta);
bool mgga_x_mspbel_registered = register_xc(
  mgga_x_mspbel_numbers, "mgga_x_mspbel", mgga_x_mspbel_params_to_numpy
);
std::vector<int> mgga_c_r2scan_numbers = {
  498, 642
};
REGISTER(mgga_c_r2scan_params, eta);
bool mgga_c_r2scan_registered = register_xc(
  mgga_c_r2scan_numbers, "mgga_c_r2scan", mgga_c_r2scan_params_to_numpy
);
std::vector<int> gga_x_rpbe_numbers = {
  117
};
REGISTER(gga_x_rpbe_params, rpbe_kappa, rpbe_mu);
bool gga_x_rpbe_registered = register_xc(
  gga_x_rpbe_numbers, "gga_x_rpbe", gga_x_rpbe_params_to_numpy
);
std::vector<int> gga_x_bpccac_numbers = {
  98
};
bool gga_x_bpccac_registered = register_xc(
  gga_x_bpccac_numbers, "gga_x_bpccac", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_xc_teter93_numbers = {
  20
};
bool lda_xc_teter93_registered = register_xc(
  lda_xc_teter93_numbers, "lda_xc_teter93", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_k_csk_numbers = {
  629, 630
};
REGISTER(mgga_k_csk_params, csk_a);
bool mgga_k_csk_registered = register_xc(
  mgga_k_csk_numbers, "mgga_k_csk", mgga_k_csk_params_to_numpy
);
std::vector<int> mgga_c_b94_numbers = {
  397, 398
};
REGISTER(mgga_c_b94_params, gamma, css, cab);
bool mgga_c_b94_registered = register_xc(
  mgga_c_b94_numbers, "mgga_c_b94", mgga_c_b94_params_to_numpy
);
std::vector<int> gga_c_cs1_numbers = {
  565
};
bool gga_c_cs1_registered = register_xc(
  gga_c_cs1_numbers, "gga_c_cs1", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_msrpbel_numbers = {
  763, 764
};
REGISTER(mgga_x_msrpbel_params, kappa, c, b, eta);
bool mgga_x_msrpbel_registered = register_xc(
  mgga_x_msrpbel_numbers, "mgga_x_msrpbel", mgga_x_msrpbel_params_to_numpy
);
std::vector<int> lda_k_gds08_worker_numbers = {
  100001
};
REGISTER(lda_k_gds08_worker_params, A, B, C);
bool lda_k_gds08_worker_registered = register_xc(
  lda_k_gds08_worker_numbers, "lda_k_gds08_worker", lda_k_gds08_worker_params_to_numpy
);
std::vector<int> mgga_x_br89_explicit_numbers = {
  586, 602
};
REGISTER(mgga_x_br89_explicit_params, gamma);
bool mgga_x_br89_explicit_registered = register_xc(
  mgga_x_br89_explicit_numbers, "mgga_x_br89_explicit", mgga_x_br89_explicit_params_to_numpy
);
std::vector<int> mgga_x_regtpss_numbers = {
  603
};
bool mgga_x_regtpss_registered = register_xc(
  mgga_x_regtpss_numbers, "mgga_x_regtpss", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_vcml_numbers = {
  651, 652
};
bool mgga_x_vcml_registered = register_xc(
  mgga_x_vcml_numbers, "mgga_x_vcml", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_k_pc07_numbers = {
  543, 634
};
REGISTER(mgga_k_pc07_params, a, b);
bool mgga_k_pc07_registered = register_xc(
  mgga_k_pc07_numbers, "mgga_k_pc07", mgga_k_pc07_params_to_numpy
);
std::vector<int> gga_x_q1d_numbers = {
  734
};
bool gga_x_q1d_registered = register_xc(
  gga_x_q1d_numbers, "gga_x_q1d", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_ncap_numbers = {
  180, 181, 324
};
REGISTER(gga_x_ncap_params, alpha, beta, mu, zeta);
bool gga_x_ncap_registered = register_xc(
  gga_x_ncap_numbers, "gga_x_ncap", gga_x_ncap_params_to_numpy
);
std::vector<int> lda_x_numbers = {
  1, 6, 549, 177
};
REGISTER(lda_x_params, alpha);
bool lda_x_registered = register_xc(
  lda_x_numbers, "lda_x", lda_x_params_to_numpy
);
std::vector<int> lda_c_epc17_numbers = {
  328, 329
};
REGISTER(lda_c_epc17_params, a, b, c);
bool lda_c_epc17_registered = register_xc(
  lda_c_epc17_numbers, "lda_c_epc17", lda_c_epc17_params_to_numpy
);
std::vector<int> gga_c_zvpbeloc_numbers = {
  606, 607, 608
};
bool gga_c_zvpbeloc_registered = register_xc(
  gga_c_zvpbeloc_numbers, "gga_c_zvpbeloc", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_m08_numbers = {
  295, 296
};
REGISTER(mgga_x_m08_params, a, b);
bool mgga_x_m08_registered = register_xc(
  mgga_x_m08_numbers, "mgga_x_m08", mgga_x_m08_params_to_numpy
);
std::vector<int> mgga_x_mbrxh_bg_numbers = {
  697
};
bool mgga_x_mbrxh_bg_registered = register_xc(
  mgga_x_mbrxh_bg_numbers, "mgga_x_mbrxh_bg", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mvs_numbers = {
  257
};
REGISTER(mgga_x_mvs_params, e1, c1, k0, b);
bool mgga_x_mvs_registered = register_xc(
  mgga_x_mvs_numbers, "mgga_x_mvs", mgga_x_mvs_params_to_numpy
);
std::vector<int> gga_x_s12_numbers = {
  495, 496
};
REGISTER(gga_x_s12_params, A, B, C, D, E, bx);
bool gga_x_s12_registered = register_xc(
  gga_x_s12_numbers, "gga_x_s12", gga_x_s12_params_to_numpy
);
std::vector<int> lda_c_lp96_numbers = {
  289, 580
};
REGISTER(lda_c_lp96_params, C1, C2, C3);
bool lda_c_lp96_registered = register_xc(
  lda_c_lp96_numbers, "lda_c_lp96", lda_c_lp96_params_to_numpy
);
std::vector<int> gga_x_lsrpbe_numbers = {
  169
};
REGISTER(gga_x_lsrpbe_params, kappa, mu, alpha);
bool gga_x_lsrpbe_registered = register_xc(
  gga_x_lsrpbe_numbers, "gga_x_lsrpbe", gga_x_lsrpbe_params_to_numpy
);
std::vector<int> gga_k_apbe_numbers = {
  185, 187, 188, 189, 190, 55
};
REGISTER(gga_k_apbe_params, kappa, mu, lambda);
bool gga_k_apbe_registered = register_xc(
  gga_k_apbe_numbers, "gga_k_apbe", gga_k_apbe_params_to_numpy
);
std::vector<int> gga_k_exp4_numbers = {
  597
};
bool gga_k_exp4_registered = register_xc(
  gga_k_exp4_numbers, "gga_k_exp4", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_pbeint_numbers = {
  60
};
REGISTER(gga_x_pbeint_params, kappa, alpha, muPBE, muGE);
bool gga_x_pbeint_registered = register_xc(
  gga_x_pbeint_numbers, "gga_x_pbeint", gga_x_pbeint_params_to_numpy
);
std::vector<int> mgga_x_2d_prhg07_numbers = {
  210
};
bool mgga_x_2d_prhg07_registered = register_xc(
  mgga_x_2d_prhg07_numbers, "mgga_x_2d_prhg07", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_cs_numbers = {
  72
};
bool mgga_c_cs_registered = register_xc(
  mgga_c_cs_numbers, "mgga_c_cs", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_am05_numbers = {
  120
};
REGISTER(gga_x_am05_params, alpha, c);
bool gga_x_am05_registered = register_xc(
  gga_x_am05_numbers, "gga_x_am05", gga_x_am05_params_to_numpy
);
std::vector<int> gga_k_pg_numbers = {
  219
};
REGISTER(gga_k_pg_params, pg_mu);
bool gga_k_pg_registered = register_xc(
  gga_k_pg_numbers, "gga_k_pg", gga_k_pg_params_to_numpy
);
std::vector<int> gga_c_regtpss_numbers = {
  83
};
bool gga_c_regtpss_registered = register_xc(
  gga_c_regtpss_numbers, "gga_c_regtpss", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_tpssloc_numbers = {
  247
};
bool mgga_c_tpssloc_registered = register_xc(
  mgga_c_tpssloc_numbers, "mgga_c_tpssloc", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_gvt4_numbers = {
  204
};
bool mgga_x_gvt4_registered = register_xc(
  mgga_x_gvt4_numbers, "mgga_x_gvt4", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_tpss_numbers = {
  231, 323, 251
};
REGISTER(mgga_c_tpss_params, beta, d, C0_c);
bool mgga_c_tpss_registered = register_xc(
  mgga_c_tpss_numbers, "mgga_c_tpss", mgga_c_tpss_params_to_numpy
);
std::vector<int> lda_c_vwn_numbers = {
  7
};
bool lda_c_vwn_registered = register_xc(
  lda_c_vwn_numbers, "lda_c_vwn", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_c_epc18_numbers = {
  330, 331
};
REGISTER(lda_c_epc18_params, a, b, c);
bool lda_c_epc18_registered = register_xc(
  lda_c_epc18_numbers, "lda_c_epc18", lda_c_epc18_params_to_numpy
);
std::vector<int> gga_x_2d_pbe_numbers = {
  129
};
bool gga_x_2d_pbe_registered = register_xc(
  gga_x_2d_pbe_numbers, "gga_x_2d_pbe", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_rppscan_numbers = {
  649
};
REGISTER(mgga_c_rppscan_params, eta);
bool mgga_c_rppscan_registered = register_xc(
  mgga_c_rppscan_numbers, "mgga_c_rppscan", mgga_c_rppscan_params_to_numpy
);
std::vector<int> gga_x_optx_numbers = {
  110
};
REGISTER(gga_x_optx_params, a, b, gamma);
bool gga_x_optx_registered = register_xc(
  gga_x_optx_numbers, "gga_x_optx", gga_x_optx_params_to_numpy
);
std::vector<int> gga_x_pw91_numbers = {
  109, 119, 316
};
REGISTER(gga_x_pw91_params, a, b, c, d, f, alpha, expo);
bool gga_x_pw91_registered = register_xc(
  gga_x_pw91_numbers, "gga_x_pw91", gga_x_pw91_params_to_numpy
);
std::vector<int> lda_c_1d_loos_numbers = {
  26
};
bool lda_c_1d_loos_registered = register_xc(
  lda_c_1d_loos_numbers, "lda_c_1d_loos", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_ityh_pbe_numbers = {
  623
};
REGISTER(gga_x_ityh_pbe_params, kappa, mu, lambda);
bool gga_x_ityh_pbe_registered = register_xc(
  gga_x_ityh_pbe_numbers, "gga_x_ityh_pbe", gga_x_ityh_pbe_params_to_numpy
);
std::vector<int> gga_x_sfat_pbe_numbers = {
  601
};
bool gga_x_sfat_pbe_registered = register_xc(
  gga_x_sfat_pbe_numbers, "gga_x_sfat_pbe", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_c_vwn_rpa_numbers = {
  8
};
bool lda_c_vwn_rpa_registered = register_xc(
  lda_c_vwn_rpa_numbers, "lda_c_vwn_rpa", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_lak_numbers = {
  342
};
bool mgga_x_lak_registered = register_xc(
  mgga_x_lak_numbers, "mgga_x_lak", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_sogga11_numbers = {
  152, 159
};
REGISTER(gga_c_sogga11_params, sogga11_a, sogga11_b);
bool gga_c_sogga11_registered = register_xc(
  gga_c_sogga11_numbers, "gga_c_sogga11", gga_c_sogga11_params_to_numpy
);
std::vector<int> gga_k_llp_numbers = {
  522, 514
};
REGISTER(gga_k_llp_params, beta, gamma);
bool gga_k_llp_registered = register_xc(
  gga_k_llp_numbers, "gga_k_llp", gga_k_llp_params_to_numpy
);
std::vector<int> mgga_x_mbrxc_bg_numbers = {
  696
};
bool mgga_x_mbrxc_bg_registered = register_xc(
  mgga_x_mbrxc_bg_numbers, "mgga_x_mbrxc_bg", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_mgga_x_pjs18_numbers = {
  706, 720
};
bool hyb_mgga_x_pjs18_registered = register_xc(
  hyb_mgga_x_pjs18_numbers, "hyb_mgga_x_pjs18", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_task_numbers = {
  707, 724
};
REGISTER(mgga_x_task_params, task_c, task_d, task_h0x, task_anu, task_bnu);
bool mgga_x_task_registered = register_xc(
  mgga_x_task_numbers, "mgga_x_task", mgga_x_task_params_to_numpy
);
std::vector<int> mgga_x_r2scan_numbers = {
  497, 645
};
REGISTER(mgga_x_r2scan_params, c1, c2, d, k1, eta, dp2);
bool mgga_x_r2scan_registered = register_xc(
  mgga_x_r2scan_numbers, "mgga_x_r2scan", mgga_x_r2scan_params_to_numpy
);
std::vector<int> gga_x_ssb_sw_numbers = {
  90, 91, 92, 312
};
REGISTER(gga_x_ssb_sw_params, A, B, C, D, E);
bool gga_x_ssb_sw_registered = register_xc(
  gga_x_ssb_sw_numbers, "gga_x_ssb_sw", gga_x_ssb_sw_params_to_numpy
);
std::vector<int> mgga_x_tau_hcth_numbers = {
  205, 279, 282
};
REGISTER(mgga_x_tau_hcth_params, cx_local, cx_nlocal);
bool mgga_x_tau_hcth_registered = register_xc(
  mgga_x_tau_hcth_numbers, "mgga_x_tau_hcth", mgga_x_tau_hcth_params_to_numpy
);
std::vector<int> lda_c_pw_numbers = {
  12, 13, 14, 25, 683, 684
};
REGISTER(lda_c_pw_params, pp, a, alpha1, beta1, beta2, beta3, beta4, fz20);
bool lda_c_pw_registered = register_xc(
  lda_c_pw_numbers, "lda_c_pw", lda_c_pw_params_to_numpy
);
std::vector<int> mgga_k_pgslb_numbers = {
  220
};
REGISTER(mgga_k_pgslb_params, pgslb_mu, pgslb_beta);
bool mgga_k_pgslb_registered = register_xc(
  mgga_k_pgslb_numbers, "mgga_k_pgslb", mgga_k_pgslb_params_to_numpy
);
std::vector<int> lda_c_w20_numbers = {
  317
};
bool lda_c_w20_registered = register_xc(
  lda_c_w20_numbers, "lda_c_w20", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_ft97_numbers = {
  114, 115
};
REGISTER(gga_x_ft97_params, beta0, beta1, beta2);
bool gga_x_ft97_registered = register_xc(
  gga_x_ft97_numbers, "gga_x_ft97", gga_x_ft97_params_to_numpy
);
std::vector<int> gga_x_fd_lb94_numbers = {
  604, 605
};
REGISTER(gga_x_fd_lb94_params, beta);
bool gga_x_fd_lb94_registered = register_xc(
  gga_x_fd_lb94_numbers, "gga_x_fd_lb94", gga_x_fd_lb94_params_to_numpy
);
std::vector<int> gga_x_sogga11_numbers = {
  151, 426
};
REGISTER(gga_x_sogga11_params, kappa, mu, a, b);
bool gga_x_sogga11_registered = register_xc(
  gga_x_sogga11_numbers, "gga_x_sogga11", gga_x_sogga11_params_to_numpy
);
std::vector<int> lda_c_vwn_4_numbers = {
  31
};
bool lda_c_vwn_4_registered = register_xc(
  lda_c_vwn_4_numbers, "lda_c_vwn_4", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_2d_prp10_numbers = {
  211
};
bool mgga_x_2d_prp10_registered = register_xc(
  mgga_x_2d_prp10_numbers, "mgga_x_2d_prp10", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mbeefvdw_numbers = {
  250
};
bool mgga_x_mbeefvdw_registered = register_xc(
  mgga_x_mbeefvdw_numbers, "mgga_x_mbeefvdw", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_vmt_numbers = {
  71, 70
};
REGISTER(gga_x_vmt_params, mu, alpha);
bool gga_x_vmt_registered = register_xc(
  gga_x_vmt_numbers, "gga_x_vmt", gga_x_vmt_params_to_numpy
);
std::vector<int> gga_x_lspbe_numbers = {
  168
};
REGISTER(gga_x_lspbe_params, kappa, mu, alpha);
bool gga_x_lspbe_registered = register_xc(
  gga_x_lspbe_numbers, "gga_x_lspbe", gga_x_lspbe_params_to_numpy
);
std::vector<int> lda_c_pmgb06_numbers = {
  590
};
bool lda_c_pmgb06_registered = register_xc(
  lda_c_pmgb06_numbers, "lda_c_pmgb06", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_tm_numbers = {
  540
};
bool mgga_x_tm_registered = register_xc(
  mgga_x_tm_numbers, "mgga_x_tm", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_k_csk_loc_numbers = {
  631, 632
};
REGISTER(mgga_k_csk_loc_params, csk_a, csk_cp, csk_cq);
bool mgga_k_csk_loc_registered = register_xc(
  mgga_k_csk_loc_numbers, "mgga_k_csk_loc", mgga_k_csk_loc_params_to_numpy
);
std::vector<int> lda_c_wigner_numbers = {
  2, 547, 548, 551, 552, 573, 574
};
REGISTER(lda_c_wigner_params, a, b);
bool lda_c_wigner_registered = register_xc(
  lda_c_wigner_numbers, "lda_c_wigner", lda_c_wigner_params_to_numpy
);
std::vector<int> mgga_c_revscan_numbers = {
  582, 585
};
bool mgga_c_revscan_registered = register_xc(
  mgga_c_revscan_numbers, "mgga_c_revscan", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_xc_zlp_numbers = {
  43
};
bool lda_xc_zlp_registered = register_xc(
  lda_xc_zlp_numbers, "lda_xc_zlp", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_rscan_numbers = {
  493
};
REGISTER(mgga_x_rscan_params, c2, d, k1, taur, alphar);
bool mgga_x_rscan_registered = register_xc(
  mgga_x_rscan_numbers, "mgga_x_rscan", mgga_x_rscan_params_to_numpy
);
std::vector<int> lda_c_pk09_numbers = {
  554
};
bool lda_c_pk09_registered = register_xc(
  lda_c_pk09_numbers, "lda_c_pk09", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_gx_numbers = {
  575
};
REGISTER(mgga_x_gx_params, c0, c1, alphainf);
bool mgga_x_gx_registered = register_xc(
  mgga_x_gx_numbers, "mgga_x_gx", mgga_x_gx_params_to_numpy
);
std::vector<int> lda_c_1d_csc_numbers = {
  18
};
REGISTER(lda_c_1d_csc_params, para, ferro, interaction, bb);
bool lda_c_1d_csc_registered = register_xc(
  lda_c_1d_csc_numbers, "lda_c_1d_csc", lda_c_1d_csc_params_to_numpy
);
std::vector<int> gga_c_bmk_numbers = {
  80, 79, 33, 280, 281, 283
};
REGISTER(gga_c_bmk_params, c_ss, c_ab);
bool gga_c_bmk_registered = register_xc(
  gga_c_bmk_numbers, "gga_c_bmk", gga_c_bmk_params_to_numpy
);
std::vector<int> lda_c_vwn_3_numbers = {
  30
};
bool lda_c_vwn_3_registered = register_xc(
  lda_c_vwn_3_numbers, "lda_c_vwn_3", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_rscan_numbers = {
  494
};
bool mgga_c_rscan_registered = register_xc(
  mgga_c_rscan_numbers, "mgga_c_rscan", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_pw86_numbers = {
  515
};
bool gga_k_pw86_registered = register_xc(
  gga_k_pw86_numbers, "gga_k_pw86", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_tb09_numbers = {
  207, 208, 209
};
REGISTER(mgga_x_tb09_params, c, alpha);
bool mgga_x_tb09_registered = register_xc(
  mgga_x_tb09_numbers, "mgga_x_tb09", mgga_x_tb09_params_to_numpy
);
std::vector<int> gga_c_op_g96_numbers = {
  85
};
bool gga_c_op_g96_registered = register_xc(
  gga_c_op_g96_numbers, "gga_c_op_g96", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_mbr_numbers = {
  716
};
REGISTER(mgga_x_mbr_params, gamma, beta, lambda);
bool mgga_x_mbr_registered = register_xc(
  mgga_x_mbr_numbers, "mgga_x_mbr", mgga_x_mbr_params_to_numpy
);
std::vector<int> mgga_x_th_numbers = {
  225
};
bool mgga_x_th_registered = register_xc(
  mgga_x_th_numbers, "mgga_x_th", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_ol1_numbers = {
  512
};
bool gga_k_ol1_registered = register_xc(
  gga_k_ol1_numbers, "gga_k_ol1", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_thakkar_numbers = {
  523
};
bool gga_k_thakkar_registered = register_xc(
  gga_k_thakkar_numbers, "gga_k_thakkar", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_vmt84_numbers = {
  69, 68
};
REGISTER(gga_x_vmt84_params, mu, alpha);
bool gga_x_vmt84_registered = register_xc(
  gga_x_vmt84_numbers, "gga_x_vmt84", gga_x_vmt84_params_to_numpy
);
std::vector<int> mgga_xc_b98_numbers = {
  598
};
bool mgga_xc_b98_registered = register_xc(
  mgga_xc_b98_numbers, "mgga_xc_b98", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_c_vwn_2_numbers = {
  29
};
bool lda_c_vwn_2_registered = register_xc(
  lda_c_vwn_2_numbers, "lda_c_vwn_2", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_c_gk72_numbers = {
  578
};
bool lda_c_gk72_registered = register_xc(
  lda_c_gk72_numbers, "lda_c_gk72", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_sfat_numbers = {
  530
};
bool gga_x_sfat_registered = register_xc(
  gga_x_sfat_numbers, "gga_x_sfat", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_k_lk_numbers = {
  617, 618
};
REGISTER(mgga_k_lk_params, kappa);
bool mgga_k_lk_registered = register_xc(
  mgga_k_lk_numbers, "mgga_k_lk", mgga_k_lk_params_to_numpy
);
std::vector<int> gga_x_n12_numbers = {
  82, 81, 32
};
REGISTER(gga_x_n12_params, CC);
bool gga_x_n12_registered = register_xc(
  gga_x_n12_numbers, "gga_x_n12", gga_x_n12_params_to_numpy
);
std::vector<int> gga_c_scan_e0_numbers = {
  553
};
bool gga_c_scan_e0_registered = register_xc(
  gga_c_scan_e0_numbers, "gga_c_scan_e0", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_pbe_numbers = {
  101, 320, 321, 102, 116, 123, 126, 140, 184, 59, 49, 45, 44, 40, 38, 265
};
REGISTER(gga_x_pbe_params, kappa, mu, lambda);
bool gga_x_pbe_registered = register_xc(
  gga_x_pbe_numbers, "gga_x_pbe", gga_x_pbe_params_to_numpy
);
std::vector<int> gga_x_b88_numbers = {
  106, 139, 149, 271, 570, 179
};
REGISTER(gga_x_b88_params, beta, gamma);
bool gga_x_b88_registered = register_xc(
  gga_x_b88_numbers, "gga_x_b88", gga_x_b88_params_to_numpy
);
std::vector<int> gga_c_gapc_numbers = {
  555
};
bool gga_c_gapc_registered = register_xc(
  gga_c_gapc_numbers, "gga_c_gapc", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_rmggac_numbers = {
  643
};
bool mgga_c_rmggac_registered = register_xc(
  mgga_c_rmggac_numbers, "mgga_c_rmggac", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_pearson_numbers = {
  511
};
bool gga_k_pearson_registered = register_xc(
  gga_k_pearson_numbers, "gga_k_pearson", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_ityh_optx_numbers = {
  622
};
REGISTER(gga_x_ityh_optx_params, a, b, gamma);
bool gga_x_ityh_optx_registered = register_xc(
  gga_x_ityh_optx_numbers, "gga_x_ityh_optx", gga_x_ityh_optx_params_to_numpy
);
std::vector<int> mgga_x_ft98_numbers = {
  319
};
REGISTER(mgga_x_ft98_params, a, b, a1, a2, b1, b2);
bool mgga_x_ft98_registered = register_xc(
  mgga_x_ft98_numbers, "mgga_x_ft98", mgga_x_ft98_params_to_numpy
);
std::vector<int> gga_x_pw86_numbers = {
  108, 144
};
REGISTER(gga_x_pw86_params, aa, bb, cc);
bool gga_x_pw86_registered = register_xc(
  gga_x_pw86_numbers, "gga_x_pw86", gga_x_pw86_params_to_numpy
);
std::vector<int> gga_c_am05_numbers = {
  135
};
REGISTER(gga_c_am05_params, alpha, gamma);
bool gga_c_am05_registered = register_xc(
  gga_c_am05_numbers, "gga_c_am05", gga_c_am05_params_to_numpy
);
std::vector<int> gga_k_tflw_numbers = {
  52, 500, 501, 502, 503, 504, 505, 506, 507, 277, 278, 508, 509, 510, 635
};
REGISTER(gga_k_tflw_params, lambda, gamma);
bool gga_k_tflw_registered = register_xc(
  gga_k_tflw_numbers, "gga_k_tflw", gga_k_tflw_params_to_numpy
);
std::vector<int> gga_x_chachiyo_numbers = {
  298
};
bool gga_x_chachiyo_registered = register_xc(
  gga_x_chachiyo_numbers, "gga_x_chachiyo", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_pkzb_numbers = {
  239
};
bool mgga_c_pkzb_registered = register_xc(
  mgga_c_pkzb_numbers, "mgga_c_pkzb", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_mgga_x_js18_numbers = {
  705
};
bool hyb_mgga_x_js18_registered = register_xc(
  hyb_mgga_x_js18_numbers, "hyb_mgga_x_js18", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_edmgga_numbers = {
  686, 695
};
bool mgga_x_edmgga_registered = register_xc(
  mgga_x_edmgga_numbers, "mgga_x_edmgga", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_x_2d_numbers = {
  19
};
bool lda_x_2d_registered = register_xc(
  lda_x_2d_numbers, "lda_x_2d", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_c_ccalda_numbers = {
  388
};
REGISTER(mgga_c_ccalda_params, c);
bool mgga_c_ccalda_registered = register_xc(
  mgga_c_ccalda_numbers, "mgga_c_ccalda", mgga_c_ccalda_params_to_numpy
);
std::vector<int> gga_x_wc_numbers = {
  118
};
bool gga_x_wc_registered = register_xc(
  gga_x_wc_numbers, "gga_x_wc", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_xc_th1_numbers = {
  196, 197, 198, 199, 154
};
REGISTER(gga_xc_th1_params, omega);
bool gga_xc_th1_registered = register_xc(
  gga_xc_th1_numbers, "gga_xc_th1", gga_xc_th1_params_to_numpy
);
std::vector<int> gga_x_kt_numbers = {
  145, 167, 146, 587
};
REGISTER(gga_x_kt_params, gamma, delta);
bool gga_x_kt_registered = register_xc(
  gga_x_kt_numbers, "gga_x_kt", gga_x_kt_params_to_numpy
);
std::vector<int> gga_c_w94_numbers = {
  561
};
bool gga_c_w94_registered = register_xc(
  gga_c_w94_numbers, "gga_c_w94", static_cast<to_numpy>(nullptr)
);
std::vector<int> hyb_gga_x_cam_s12_numbers = {
  646, 647
};
REGISTER(hyb_gga_x_cam_s12_params, A, B, C, D, E);
bool hyb_gga_x_cam_s12_registered = register_xc(
  hyb_gga_x_cam_s12_numbers, "hyb_gga_x_cam_s12", hyb_gga_x_cam_s12_params_to_numpy
);
std::vector<int> lda_x_sloc_numbers = {
  692
};
REGISTER(lda_x_sloc_params, a, b);
bool lda_x_sloc_registered = register_xc(
  lda_x_sloc_numbers, "lda_x_sloc", lda_x_sloc_params_to_numpy
);
std::vector<int> lda_c_pw_erf_numbers = {
  654
};
bool lda_c_pw_erf_registered = register_xc(
  lda_c_pw_erf_numbers, "lda_c_pw_erf", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_sa_tpss_numbers = {
  542
};
bool mgga_x_sa_tpss_registered = register_xc(
  mgga_x_sa_tpss_numbers, "mgga_x_sa_tpss", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_gaploc_numbers = {
  556
};
bool gga_c_gaploc_registered = register_xc(
  gga_c_gaploc_numbers, "gga_c_gaploc", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_p86_numbers = {
  132, 217
};
REGISTER(gga_c_p86_params, malpha, mbeta, mgamma, mdelta, aa, bb, ftilde);
bool gga_c_p86_registered = register_xc(
  gga_c_p86_numbers, "gga_c_p86", gga_c_p86_params_to_numpy
);
std::vector<int> mgga_x_mggac_numbers = {
  711
};
bool mgga_x_mggac_registered = register_xc(
  mgga_x_mggac_numbers, "mgga_x_mggac", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_mpbe_numbers = {
  616, 595, 596
};
REGISTER(gga_k_mpbe_params, a, c1, c2, c3);
bool gga_k_mpbe_registered = register_xc(
  gga_k_mpbe_numbers, "gga_k_mpbe", gga_k_mpbe_params_to_numpy
);
std::vector<int> mgga_c_vsxc_numbers = {
  232
};
REGISTER(mgga_c_vsxc_params, alpha_ss, alpha_ab, dss, dab);
bool mgga_c_vsxc_registered = register_xc(
  mgga_c_vsxc_numbers, "mgga_c_vsxc", mgga_c_vsxc_params_to_numpy
);
std::vector<int> mgga_x_rlda_numbers = {
  688, 230, 243
};
REGISTER(mgga_x_rlda_params, prefactor);
bool mgga_x_rlda_registered = register_xc(
  mgga_x_rlda_numbers, "mgga_x_rlda", mgga_x_rlda_params_to_numpy
);
std::vector<int> gga_c_sg4_numbers = {
  534
};
bool gga_c_sg4_registered = register_xc(
  gga_c_sg4_numbers, "gga_c_sg4", static_cast<to_numpy>(nullptr)
);
std::vector<int> lda_k_tf_numbers = {
  50, 51
};
REGISTER(lda_k_tf_params, ax);
bool lda_k_tf_registered = register_xc(
  lda_k_tf_numbers, "lda_k_tf", lda_k_tf_params_to_numpy
);
std::vector<int> gga_x_pbe_erf_gws_numbers = {
  655, 656
};
REGISTER(gga_x_pbe_erf_gws_params, kappa, b_PBE, ax, omega);
bool gga_x_pbe_erf_gws_registered = register_xc(
  gga_x_pbe_erf_gws_numbers, "gga_x_pbe_erf_gws", gga_x_pbe_erf_gws_params_to_numpy
);
std::vector<int> hyb_mgga_xc_wb97mv_numbers = {
  531
};
REGISTER(hyb_mgga_xc_wb97mv_params, c_x, c_ss, c_os);
bool hyb_mgga_xc_wb97mv_registered = register_xc(
  hyb_mgga_xc_wb97mv_numbers, "hyb_mgga_xc_wb97mv", hyb_mgga_xc_wb97mv_params_to_numpy
);
std::vector<int> gga_k_lc94_numbers = {
  521
};
REGISTER(gga_k_lc94_params, a, b, c, d, f, alpha, expo);
bool gga_k_lc94_registered = register_xc(
  gga_k_lc94_numbers, "gga_k_lc94", gga_k_lc94_params_to_numpy
);
std::vector<int> gga_xc_th2_numbers = {
  155
};
bool gga_xc_th2_registered = register_xc(
  gga_xc_th2_numbers, "gga_xc_th2", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_m11_l_numbers = {
  226
};
REGISTER(mgga_x_m11_l_params, a, b, c, d);
bool mgga_x_m11_l_registered = register_xc(
  mgga_x_m11_l_numbers, "mgga_x_m11_l", mgga_x_m11_l_params_to_numpy
);
std::vector<int> mgga_k_rda_numbers = {
  621
};
REGISTER(mgga_k_rda_params, A0, A1, A2, A3, beta1, beta2, beta3, a, b, c);
bool mgga_k_rda_registered = register_xc(
  mgga_k_rda_numbers, "mgga_k_rda", mgga_k_rda_params_to_numpy
);
std::vector<int> gga_x_lv_rpw86_numbers = {
  58
};
bool gga_x_lv_rpw86_registered = register_xc(
  gga_x_lv_rpw86_numbers, "gga_x_lv_rpw86", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_eel_numbers = {
  326
};
REGISTER(mgga_x_eel_params, c, x0, a0);
bool mgga_x_eel_registered = register_xc(
  mgga_x_eel_numbers, "mgga_x_eel", mgga_x_eel_params_to_numpy
);
std::vector<int> mgga_x_pbe_gx_numbers = {
  576
};
bool mgga_x_pbe_gx_registered = register_xc(
  mgga_x_pbe_gx_numbers, "mgga_x_pbe_gx", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_x_hjs_b88_v2_numbers = {
  46
};
REGISTER(gga_x_hjs_b88_v2_params, a, b);
bool gga_x_hjs_b88_v2_registered = register_xc(
  gga_x_hjs_b88_v2_numbers, "gga_x_hjs_b88_v2", gga_x_hjs_b88_v2_params_to_numpy
);
std::vector<int> gga_x_wpbeh_numbers = {
  524
};
bool gga_x_wpbeh_registered = register_xc(
  gga_x_wpbeh_numbers, "gga_x_wpbeh", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_k_dk_numbers = {
  516, 517, 518, 519, 520
};
REGISTER(gga_k_dk_params, aa, bb);
bool gga_k_dk_registered = register_xc(
  gga_k_dk_numbers, "gga_k_dk", gga_k_dk_params_to_numpy
);
std::vector<int> mgga_x_m11_numbers = {
  297, 304
};
REGISTER(mgga_x_m11_params, a, b);
bool mgga_x_m11_registered = register_xc(
  mgga_x_m11_numbers, "mgga_x_m11", mgga_x_m11_params_to_numpy
);
std::vector<int> gga_c_q2d_numbers = {
  47
};
bool gga_c_q2d_registered = register_xc(
  gga_c_q2d_numbers, "gga_c_q2d", static_cast<to_numpy>(nullptr)
);
std::vector<int> gga_c_pw91_numbers = {
  134
};
bool gga_c_pw91_registered = register_xc(
  gga_c_pw91_numbers, "gga_c_pw91", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_scan_numbers = {
  263, 264, 581, 583
};
REGISTER(mgga_x_scan_params, c1, c2, d, k1);
bool mgga_x_scan_registered = register_xc(
  mgga_x_scan_numbers, "mgga_x_scan", mgga_x_scan_params_to_numpy
);
std::vector<int> gga_k_rational_p_numbers = {
  218
};
REGISTER(gga_k_rational_p_params, C2, p);
bool gga_k_rational_p_registered = register_xc(
  gga_k_rational_p_numbers, "gga_k_rational_p", gga_k_rational_p_params_to_numpy
);
std::vector<int> mgga_x_2d_js17_numbers = {
  609
};
bool mgga_x_2d_js17_registered = register_xc(
  mgga_x_2d_js17_numbers, "mgga_x_2d_js17", static_cast<to_numpy>(nullptr)
);
std::vector<int> mgga_x_jk_numbers = {
  256
};
REGISTER(mgga_x_jk_params, beta, gamma);
bool mgga_x_jk_registered = register_xc(
  mgga_x_jk_numbers, "mgga_x_jk", mgga_x_jk_params_to_numpy
);
std::vector<int> gga_x_bayesian_numbers = {
  125
};
bool gga_x_bayesian_registered = register_xc(
  gga_x_bayesian_numbers, "gga_x_bayesian", static_cast<to_numpy>(nullptr)
);

// One function to convert them all

py::dict get_p(uint64_t xc_func) {
  xc_func_type* func = reinterpret_cast<xc_func_type*>(xc_func);
  py::dict ret;
  int number = func->info->number;
  ret["number"] = number;
  ret["libxc_name"] = std::string(func->info->name);
  ret["cam_omega"] = func->cam_omega;
  ret["cam_alpha"] = func->cam_alpha;
  ret["cam_beta"] = func->cam_beta;
  ret["nlc_b"] = func->nlc_b;
  ret["nlc_C"] = func->nlc_C;
  // thresholds
  ret["dens_threshold"] = func->dens_threshold;
  ret["zeta_threshold"] = func->zeta_threshold;
  ret["sigma_threshold"] = func->sigma_threshold;
  ret["tau_threshold"] = func->tau_threshold;
  // params
  auto it = registry.find(number);
  if (it == registry.end()) {
    // Functional not in registry (e.g., no Maple code)
    ret["params"] = std::map<std::string, py::array>();
    ret["maple_name"] = "";
  } else {
    const auto& entry = it->second;
    to_numpy get_params = entry.second;
    const std::string& maple_name = entry.first;
    if (get_params != nullptr && func->params != nullptr) {
       auto params_map = get_params(func);

       // Inject derived CAM parameters for functionals that need them
       // hyb_gga_x_cam_s12 (XC 646, 647) needs bx = 1.0 - cam_alpha
       if (number == 646 || number == 647) {
         double bx = 1.0 - func->cam_alpha;
         params_map["bx"] = ToNumpy(bx);
       }

       ret["params"] = params_map;
    } else {
       ret["params"] = std::map<std::string, py::array>();
    }
    ret["maple_name"] = maple_name;
  }
  ret["nspin"] = func->nspin;
  // mix function
  if (func->n_func_aux > 0 && func->func_aux != nullptr) {
    py::list l;
    for (int i = 0; i < func->n_func_aux; ++i) {
      if (func->func_aux[i] != nullptr) {
        l.append(get_p(reinterpret_cast<uint64_t>(func->func_aux[i])));
      }
    }
    if (l.size() > 0) {
      ret["func_aux"] = l;
      std::vector<double> mix_coef(func->mix_coef, func->mix_coef + func->n_func_aux);
      ret["mix_coef"] = mix_coef;
    }
  }
  return ret;
}

PYBIND11_MODULE(helper, m) {
  m.doc() = "Helper to extract libxc params.";  // optional module docstring
  m.def("get_p", &get_p);
}