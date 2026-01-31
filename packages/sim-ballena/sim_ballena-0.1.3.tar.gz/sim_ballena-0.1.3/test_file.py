import sim_ballena as ballena
import matplotlib.pyplot as plt


net = (ballena.Network( [ballena.Lif().tau(5),ballena.Lif().tau(0.2)] )
       .synapses_net([])
       .weights_net([])
       .outputs([1])
       .mode(['VOLTAGES','SPIKES']))



# ==========
#   STEP 1
# ==========
net = net.synapses_in([(0,0),(0,1)])
net = net.weights_in([10,10])

times = [ (1, 0) ]
instance = ballena.Instance( times )
res = net.simulate( instance, 2 )

time = res.time()
volt = res.voltages()

plt.figure(figsize=(10,5))
plt.subplot(121)
plt.ylim(-80,-55)
plt.plot( time, volt[0], label='true')
# plt.subplot(122)
# plt.ylim(-80,-55)
# plt.plot( time, volt[1], label='true')

plt.show()



