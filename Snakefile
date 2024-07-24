# List of all experiments that should be plot

# These do not work yet:  tau7 tau8
# This has nco file not accepted by this implementation: dlayer tau2pl tau1
EXP = "cp1l cp4b cp7h".split() + " ".split() + "arc1 arc_dlayer ".split() + "beata bella lace othia".split()
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
    