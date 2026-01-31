import sim_ballena as ballena
import matplotlib.pyplot as plt


net = (ballena.Network( ballena.Lif().tau(5).t_refractory(0).repeat(2) )
       .synapses_net([])
       .weights_net([])
       .outputs([0,1])
       .mode(['VOLTAGES','SPIKES']))



# ==========
#   STEP 1
# ==========
net = net.synapses_in([(0,0),(0,1),(1,0),(1,1)])
net = net.weights_in([16,0,-16,0])

times = [ (1, 0), (5, 1) ]
instance = ballena.Instance( times )
res = net.simulate( instance, 10 )

time = res.time()
volt = res.voltages() 
plt.figure(figsize=(10,4))
plt.subplot(121)
plt.plot( time, volt[0], label='true')
plt.subplot(122)
plt.plot( time, volt[1], label='false')
plt.show()

# ==========
#   STEP 1
# ==========
net = net.weights_in([16,0,-16,0])

times = [ (1, 0), (5, 1) ]
instance = ballena.Instance( times )
res = net.simulate( instance, 10 )

time = res.time()
volt = res.voltages() 
plt.figure(figsize=(10,4))
plt.subplot(121)
plt.plot( time, volt[0], label='true')
plt.subplot(122)
plt.plot( time, volt[1], label='false')
plt.show()

