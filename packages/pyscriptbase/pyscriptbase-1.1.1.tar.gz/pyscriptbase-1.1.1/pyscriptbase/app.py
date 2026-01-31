def getAssistedList(receivers: list[tuple], senders: list[tuple], maxCount: int = 1) -> list[tuple]:
    result = []
    sendMap = {}

    for sender in senders:
        for _ in range(0, sender[1]):
            for j, receiver in enumerate(receivers):
                if receiver[0] == sender[0] or receiver[1] == 0:
                    continue
                key = f"{sender[0]}-{receiver[0]}"
                if key not in sendMap:
                    sendMap[key] = 0
                if sendMap[key] >= maxCount:
                    continue
                sendMap[key] += 1
                receivers[j] = (receiver[0], receiver[1] - 1)
                result.append((sender[0], receiver[0]))
                break
    return result
