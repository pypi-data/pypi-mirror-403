import Ballena as ballena


# ======================
#    CREAR OBJETOS
# ======================

instance = [(0.4, 0), 
            (0.5, 1),
            (2.1, 0),
            (3.0, 0), 
            (3.4, 1)] # [ (TIME, INPUT_ID) ... ]

instance = ballena.create_input( instance ) # WRAPPER

synapses_in  = [(0,1),(0,2),(1,1)]  # [ (neu_pre, neu_post) ... ]
synapses_net = [(0,1),(0,2),(2,1)]  # [ (neu_pre, neu_post) ... ]
weights_in   = [0,1,2]                # [ w1,w2,w3 ... ]
weights_net   = [3,4,5]

neurons  = [ballena.lif(tau=2, v_thres=-55, v_rest=-70, refract=5),
            ballena.lif(tau=3, ),
            ballena.lif(tau=4, )]

outputs = [2]

# ======================
#  CREAR RED Y SIMULAR
# ======================

net = (ballena.network(neurons)
            .set_synpases_in(synapses_in)
            .set_synpases_net(synapses_net)
            .set_weights_in(weights_in)
            .set_weights_net(weights_net)
            .set_outputs(outputs))

spikes = net.simulate( instance, t=300 ).get_spikes()




# ===========================================
# CASO DE USO EVALUAR ACCURACY CON SPIKES
# ===========================================

net = (
    ballena.network(neurons)
            .set_synpases_in(synapses_in)
            .set_synpases_net(synapses_net)
            .set_outputs([10,11,12])         # Topologia de la red fija
)

def evaluar_weights(weights):                # Esta pudiera ser una funcion objetivo
    net.set_weights( weights )
    
    resultados = [ net.simulate(instance, t=10).get_spikes() for instance in dataset ]
    return accuracy(resultados, dataset)

# =============================
# CASO DE USO PLOTEAR RESPUESTA
# =============================
net = (
    ballena.network(neurons)
    .set_synpases_in(synapses_in)
    .set_synpases_net(synapses_net)
    .net.set_weights( weights )
    .set_outputs([1])
)

voltage = net.simulate(instance, t=10).get_voltage()
plt.plot(voltage[0])


# ==========================
# CASO DE USO NEUROEVOLUCION 
# ==========================

net = ballena.network(neurons).set_synapses_in(synapses_in).set_outputs([2,3])

def evaluar_topologia(synapses, weights):
    net.set_synapses_net(synapses).set_weights(weights)

    resultados = [ net.simulate(instance, t=10).spikes() for instance in dataset ]
    return accuracy(resultados, dataset)



# ==================================
# CASO DE USO NEUROEVOLUCION
#    CON AJUSTE AUTOMATICO DE PESOS 
# ==================================

net = (
    ballena.network(neurons)
    .set_synapses_in(synapses_in)
    .set_outputs([2,3])
    .stdp( True )               # Ajuste automatico
)

def evaluar_topologia(synapses):
    net.set_synapses_net(synapses)  # se contruye topologia

    for e in range(epochs):         # Se ajustan los pesos
        for instancia in dataset.train():
            res = net.simulate( instancia, t=10 ).get_spikes()    # pass forward
            err = calcular_error(res,instancia)                   # loss function
            net.dopamina( err )                                   # ajuste pesos
    
    res = [ net.simulate(instancia, t=10) for instancia in dataset.validation() ]
    return acc(res, dataset.validation())
    

