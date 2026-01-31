import sim_ballena as ballena
import matplotlib.pyplot as plt
import random
import time

inputs = ballena.Instance( [(40*t/100,0) for t in range(1,100)] )
n = [ballena.Lif().tau(10).t_refractory(0.001)]
syn_in  = [(0,0)]
syn_net = []
w_in    = [4] 
w_net   = []
outputs = [0]

# ========================
#  RED QUE GRABA VOLTAJES
# ========================
net = (ballena.Network(n)
       .synapses_in(syn_in)
       .synapses_net(syn_net)
       .weights_in(w_in)
       .weights_net(w_net)
       .outputs(outputs)
       .mode(['VOLTAGES','SPIKES']))

start = time.time()
for _ in range(5000):
       res = net.simulate( inputs, 40  )
print(f"{time.time()-start}")

# ========================
#  RED QUE NO GRABA 
# ========================
net = (ballena.Network(n)
       .synapses_in(syn_in)
       .synapses_net(syn_net)
       .weights_in(w_in)
       .weights_net(w_net)
       .outputs(outputs)
       .mode(['SPIKES']))

start = time.time()
for _ in range(5000):
       res = net.simulate( inputs, 40  )
print(f"{time.time()-start}")





# inputs_ = [(t/4,0) for t in range(1,40)]
# inputs = ballena.Instance(inputs_)

# n = [ballena.Lif().tau(10).t_refractory(2),
#      ballena.Lif().tau(20)]
# syn_in  = [(0,0)]
# syn_net = [(0,1)]
# w_in    = [4] 
# w_net   = [9]
# outputs = [0,1]

# net = (ballena.Network(n)
#        .synapses_in(syn_in)
#        .synapses_net(syn_net)
#        .weights_in(w_in)
#        .weights_net(w_net)
#        .outputs(outputs)
#        .mode(['VOLTAGES','SPIKES']))

# res = net.simulate( inputs, 11  )

# time = res.time()
# volt = res.voltages()

# print( res.spikes() )

# plt.plot( time,volt[0], label=f'neu {outputs[0]}' )
# plt.plot( time,volt[1], label=f'neu {outputs[1]}' )
# plt.vlines(res.spikes()[0], -70, -55, linestyles='dashed', colors='red')
# plt.legend()
# plt.grid()
# plt.show()