#!/usr/bin/env python3

import mltk

if __name__ == '__main__':
    client = mltk.MLStorageClient('http://mlserver.ipwx.me:7980/')
    for doc in client.query('status:RUNNING'):
        print(f'http://mlserver.ipwx.me:7980/{doc["id"]}')
