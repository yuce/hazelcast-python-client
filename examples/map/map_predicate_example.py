import hazelcast

from hazelcast.predicate import between

client = hazelcast.HazelcastClient()

predicate_map = client.get_map("predicate-map").blocking()
for i in range(10):
    predicate_map.put("key" + str(i), i)

predicate = between("this", 3, 5)

entry_set = predicate_map.entry_set(predicate)

for key, value in entry_set:
    print("%s -> %s" % (key, value))

client.shutdown()
