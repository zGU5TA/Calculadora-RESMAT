# ==============================================================================
# DADOS FIXOS: materiais, unidades e cores da interface
# ==============================================================================

# Banco de dados de materiais (valores no SI: Pa)
#   E       -> módulo de elasticidade
#   sigma_y -> tensão de escoamento
#   tau_adm -> tensão de cisalhamento admissível (usada nos pinos/rebites)
MATERIALS_DB = {
    "Aço Estrutural A36": {"E": 200e9, "sigma_y": 250e6, "tau_adm": 145e6},
    "Aço Inoxidável 304": {"E": 193e9, "sigma_y": 215e6, "tau_adm": 125e6},
    "Alumínio 6061-T6": {"E": 68.9e9, "sigma_y": 276e6, "tau_adm": 150e6},
    "Alumínio 7075-T6": {"E": 71.7e9, "sigma_y": 503e6, "tau_adm": 220e6},
    "Latão C36000": {"E": 97e9, "sigma_y": 310e6, "tau_adm": 160e6},
    "Cobre C11000": {"E": 117e9, "sigma_y": 230e6, "tau_adm": 120e6},
    "Liga de Titânio Ti-6Al-4V": {"E": 114e9, "sigma_y": 880e6, "tau_adm": 550e6},
    "Ferro Fundido Cinzento": {"E": 100e9, "sigma_y": 150e6, "tau_adm": 90e6},
    "Madeira Pinho/Eucalipto": {"E": 12e9, "sigma_y": 40e6, "tau_adm": 10e6},
    "Polímero Fibra Carbono": {"E": 150e9, "sigma_y": 600e6, "tau_adm": 300e6},
}

# Nome da opção em que o usuário digita as propriedades
PERSONALIZADO = "Personalizado"

# Conversor de unidades: quanto 1 unidade vale no SI (N, m ou Pa)
UNITS = {
    "force": {"kN": 1e3, "N": 1.0, "kgf": 9.80665, "lbf": 4.44822},
    "pos": {"m": 1.0, "cm": 0.01, "mm": 0.001},
    "dim": {"mm": 0.001, "cm": 0.01, "m": 1.0},
    "stress": {"MPa": 1e6, "GPa": 1e9, "Pa": 1.0, "psi": 6894.76, "N/mm²": 1e6},
}

# Unidade em que as tensões aparecem nos resultados
UNIDADE_TENSAO = "MPa"

# Paleta de cores da interface (tema escuro)
CORES = {
    "fundo": "#1E1E2E",
    "painel": "#181825",
    "campo": "#313244",
    "botao": "#45475A",
    "botao_ativo": "#585B70",
    "texto": "#CDD6F4",
    "texto_suave": "#BAC2DE",
    "cinza": "#A6ADC8",
    "separador": "#45475A",
    "azul": "#89B4FA",
    "laranja": "#FAB387",
    "verde": "#A6E3A1",
    "vermelho": "#F38BA8",
    "amarelo": "#F9E2AF",
    "erro_campo": "#5C2B3A",
}
