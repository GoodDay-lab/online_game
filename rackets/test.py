# import sys

# sys.path.append('..')
# from app.client import Client, Cache


# cache = Cache()
# client = Client(cache)

# SERVER_ADDRESS = "127.0.0.1", 9000
# client.call_udp(method='connect', address=SERVER_ADDRESS, response=True, cookie=['uid'])
# client.call_udp(method="create_session", address=SERVER_ADDRESS, response=True, cookie=['sid'])
# client.call_udp(method="send_msg", data={'msg': "hello!"}, address=SERVER_ADDRESS)
# print(client.call_udp(method="get_msg", address=SERVER_ADDRESS, response=True))


def delimite_message(message):
        rows = [[]]
        cur_len = 0
        
        for word in message.split():
            if cur_len + len(word) > 24:
                rows.append([])
                cur_len = 0
            rows[-1].append(word)
            cur_len += len(word) + 1
        
        return rows[:6]


for line in delimite_message("Hello, how are you? I am nice thanks attention how your dog? mm?"):
    print(line)
