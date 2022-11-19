# import required module
import os
# assign directory
directory = 'worker/output/mdx_extra_q/short-hop'

test_list = ["test1", "test2", "test3"]
# # iterate over files in
# # that directory
# if os.path.exists("worker/output/mdx_extra_q"):
#     for filename in os.listdir(directory):
#         f = os.path.join(directory, filename)
#         # checking if it is a file
#         if os.path.isfile(f):
#             print(f)

print(test_list)

# for item in test_list:
#     print("hi")
#     print(item)
#     test_list.pop(0)

while len(test_list) > 0:
    newItem = test_list.pop(0)
    print(newItem)
print(test_list)