# List of all experiments that should be plot
EXP_COMMON = "cp4b cp7h".split() + "tau1".split() + "arc_dlayer".split() + "beata bella lace othia".split()
EXP_UHF = EXP_COMMON + "cp1l arc1 dlayer tau2pl".split()
EXP_VHF = EXP_COMMON + "tau7 tau8".split()
            
rule all:
    input:
        expand("kst/exp/{name}/{name}.elan", name=EXP_UHF),
        expand("plot/{name}-u.png", name=EXP_UHF),
        expand("kst/exp/{name}/{name}.elan", name=EXP_VHF),
        expand("plot/{name}-v.png", name=EXP_VHF)
     
rule make_plot_uhf:
    input: "kst/exp/{name}/{name}.elan"
    output: 'plot/{name}-u.png'
    log: 'logs/make_plot_{name}.log'
    shell: 'python -m src {input} UHF 1 plot'
    
rule make_plot_vhf:
    input: "kst/exp/{name}/{name}.elan"
    output: 'plot/{name}-v.png'
    log: 'logs/make_plot_{name}.log'
    shell: 'python -m src {input} VHF 1 plot'
    
    