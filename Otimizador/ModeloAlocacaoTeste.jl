using Pkg
Pkg.add("JuMP")
Pkg.add("GLPK")
using JuMP
using GLPK

ativos = ["Ativo A", "Ativo B", "Ativo C"]
classes = ["Renda Fixa", "Renda Variável", "Renda Fixa"]
limites = [0.5, 0.4, 0.6]
patrimonio_total = 1_000_000
restricoes_classes = Dict(
	    "Renda Fixa" => (0.4, 0.8),
	    "Renda Variável" => (0.3, 0.6)
	)
modelo = Model(GLPK.Optimizer)
n_ativos = length(ativos)
@variable(modelo, 0 <= alocacao[i = 1:n_ativos] <= limites[i] * patrimonio_total)
@constraint(modelo, sum(alocacao[i] for i in 1:n_ativos) == patrimonio_total)
for (classe, (min_limite, max_limite)) in restricoes_classes
    total_classe = sum(alocacao[i] for i in 1:n_ativos if classes[i] == classe)
    @constraint(modelo, total_classe >= min_limite * patrimonio_total)
    @constraint(modelo, total_classe <= max_limite * patrimonio_total)
end
@objective(modelo, Max, sum(alocacao[i] for i in 1:n_ativos if classes[i] == "Renda Fixa"))
optimize!(modelo)
if termination_status(modelo) == MOI.OPTIMAL
    println("Alocação ótima:")
    for i in 1:n_ativos
        println("$ativos[i]: R\$ $(value(alocacao[i]))")
    end
else
    println("Solução não encontrada")
    println("Status: ", termination_status(modelo))
end