from urllib.request import Request, urlopen, ssl, socket
import json, sys, datetime, argparse

date_fmt = r'%b %d %H:%M:%S %Y %Z'

def init_parser():
  """Parsing input parameters.

  Returns:
  A dict mapping keys to the input script arguments.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument('-urls', nargs='+', help='site(s) to check cert without http(s)')
  parser.add_argument('-delta', type=int, default=10, help='Delta days to check. By default - 10')
  return parser

def getCertificatExpirationDate(hostname, ssl_date_fmt):
  """Open ssl port and get certificate

  Returns:
  Certificate expired date 
  <class 'datetime.datetime'>
  """
  context = ssl.create_default_context()
  
  try:
      conn = socket.create_connection((hostname, '443'))
      open_sock = context.wrap_socket(conn, server_hostname=hostname)
      data = json.dumps(open_sock.getpeercert())
  except:
      print("Error", sys.exc_info())
      raise
  date = datetime.datetime.strptime(json.loads(data)['notAfter'], ssl_date_fmt)
  return date

def main():
  namespace = init_parser().parse_args()
  print('Delta days:', namespace.delta)
  for url in namespace.urls:
    print("Checking url:   ", url)
    expDate = getCertificatExpirationDate(url,date_fmt)
    print("Expiration date:", expDate)
    print("Current date:   ", datetime.datetime.today())
    if expDate > datetime.datetime.today() + datetime.timedelta(days=namespace.delta):
      print('OK!')
    else:
      print("Warning")
      sys.exit('Certificate expires soon')

if (__name__ == '__main__'):
  main()
