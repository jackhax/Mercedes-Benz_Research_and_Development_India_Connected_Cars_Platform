import json
import urllib3

http = urllib3.PoolManager()

dist = 'restmock.techgig.com/merc/distance'
charge = 'https://restmock.techgig.com/merc/charge_level'
cstations = 'https://restmock.techgig.com/merc/charging_stations'


def isChargingRequired(stations, fuel, dist):
    if (dist < fuel):
        return False
    i = 0
    for s in stations:
        if (int(s['distance']) > fuel):
            return -1
        fuel += int(s['limit'])
        i += 1
        if (fuel >= dist):
            break
    if (i == 0):    return -1
    return i


def lambda_handler(event, context):
    tid = 0
    # vin = event['queryStringParameters']['vin']
    # frm = event['queryStringParameters']['from']
    # to = event['queryStringParameters']['to']

    vin = event['vin']
    frm = event['from']
    to = event['to']

    distanceReq = {"source": str(frm), "destination": str(to)}
    charge_level = {"vin": str(vin)}

    # r = requests.post(url = dist,json=distanceReq)
    # s = requests.post(url = charge,json=charge_level)

    r = json.loads(
        http.request('POST', dist, body=json.dumps(distanceReq), headers={'Content-Type': 'application/json'}).data)
    s = json.loads(
        http.request('POST', charge, body=json.dumps(charge_level), headers={'Content-Type': 'application/json'}).data)
    t = json.loads(
        http.request('POST', cstations, body=json.dumps(distanceReq),
                     headers={'Content-Type': 'application/json'}).data)

    if (r['error'] or s['error'] or t['error']):
        response = {}
        response['transactionId'] = 1
        response['errors'] = [{"id": 9999, "description": "Technical Exception"}]

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    distance = int(r['distance'])
    chargeLevel = int(s['currentChargeLevel'])
    stations = t['chargingStations']

    chargeRequired = isChargingRequired(stations, chargeLevel, distance)

    response = {}
    response['vin'] = vin
    response['source'] = frm
    response['destination'] = to
    response['distance'] = str(r['distance'])
    response['currentChargeLevel'] = str(s['currentChargeLevel'])

    if chargeRequired == False:
        response['isChargingRequired'] = False
        tid = 2
    else:
        tid = 3
        response['isChargingRequired'] = True
        if (chargeRequired == -1):
            response['errors'] = [
                {"id": 8888, "description": "Unable to reach the destination with the current fuel level"}]
        else:
            chargingStation = []
            for z in range(chargeRequired):
                chargingStation.append(stations[z])
            response['chargingStations'] = chargingStation

    response['transactionId'] = tid

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
