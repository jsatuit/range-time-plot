# List of all experiments that should be plot

# These do not work yet:   tau8
EXP = "cp1l cp4b cp7h".split() + "tau1 tau2pl tau7 ".split() + "arc1 arc_dlayer dlayer".split() + "beata bella lace othia".split()
#EXP = "beata bella manda".split()
            
rule all:
    input: 
        expand("kst/exp/{name}/{name}.elan", name=EXP),
        expand("plot/{name}.png", name=EXP)
     
rule make_plot:
    input: "kst/exp/{name}/{name}.elan"
    output: 'plot/{name}.png'
    log: 'logs/make_plot_{name}.log'
    shell: 'python -m src {input} 1 {output}'
    