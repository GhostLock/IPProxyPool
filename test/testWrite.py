import sys
import time

write, flush = sys.stdout.write, sys.stdout.flush
str = 'IPProxyPool----->>>>>>>>initializing'
write(str)
flush()
time.sleep(1)
write('\x08' * len(str))

str2 = 'IPProxyPool----->>>>>>>>db exists ip:%d' % 2
str2 += '\r\nIPProxyPool----->>>>>>>>now ip num < MINNUM,start crawling...'
write(str2 + "\r\n")
flush()
time.sleep(0.5)

