import hashlib
import base64
import time
import random
from typing import Optional

STD_B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
CUSTOM_B64 = 'Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe'

ENC_MAP = {STD_B64[i]: CUSTOM_B64[i] for i in range(len(STD_B64))}

def custom_b64(buf):
    b64 = base64.b64encode(buf).decode()
    return ''.join(ENC_MAP.get(ch, ch) for ch in b64)

def md5(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).digest()

def rc4(key, pt):
    s = list(range(256))
    j = 0
    kl = len(key)
    for i in range(256):
        j = (j + s[i] + key[i % kl]) & 0xff
        s[i], s[j] = s[j], s[i]
    
    out = bytearray(len(pt))
    i = j = 0
    for n in range(len(pt)):
        i = (i + 1) & 0xff
        j = (j + s[i]) & 0xff
        s[i], s[j] = s[j], s[i]
        k = s[(s[i] + s[j]) & 0xff]
        out[n] = pt[n] ^ k
    return bytes(out)

def xor_buf(buf):
    result = 0
    for b in buf:
        result ^= b
    return result

def xbogus(p, d, ua, ts):
    uk = bytes([0x00, 0x01, 0x0e])
    lk = bytes([0xff])
    fv = 0x4a41279f
    mp = md5(md5(p.encode()))
    md_d = md5(md5(d.encode()))
    urc = rc4(uk, ua.encode())
    ub64 = base64.b64encode(urc)
    mu = md5(ub64)
    
    parts = [
        bytes([0x40]),
        uk,
        mp[14:16],
        md_d[14:16],
        mu[14:16],
        ts.to_bytes(4, 'big'),
        fv.to_bytes(4, 'big')
    ]
    buf = b''.join(parts)
    cs = xor_buf(buf)
    buf = buf + bytes([cs])
    enc = bytes([0x02]) + lk + rc4(lk, buf)
    return custom_b64(enc)

aa = [
    0xFFFFFFFF, 138, 1498001188, 211147047, 253, None, 203, 288, 9,
    1196819126, 3212677781, 135, 263, 193, 58, 18, 244, 2931180889, 240, 173,
    268, 2157053261, 261, 175, 14, 5, 171, 270, 156, 258, 13, 15, 3732962506,
    185, 169, 2, 6, 132, 162, 200, 3, 160, 217618912, 62, 2517678443, 44, 164,
    4, 96, 183, 2903579748, 3863347763, 119, 181, 10, 190, 8, 2654435769, 259,
    104, 230, 128, 2633865432, 225, 1, 257, 143, 179, 16, 600974999, 185100057,
    32, 188, 53, 2718276124, 177, 196, 4294967296, 147, 117, 17, 49, 7, 28, 12,
    266, 216, 11, 0, 45, 166, 247, 1451689750
]
ot = [aa[9], aa[69], aa[51], aa[92]]

def init_prng():
    now = int(time.time() * 1000)
    return [
        aa[44], aa[74], aa[10], aa[62], aa[42], aa[17], aa[2], aa[21],
        aa[3], aa[70], aa[50], aa[32],
        aa[0] & now,
        random.randint(0, aa[77] - 1),
        random.randint(0, aa[77] - 1),
        random.randint(0, aa[77] - 1)
    ]

kt = init_prng()
st = aa[88]

def u32(x):
    return x & 0xFFFFFFFF

def rotl(x, n):
    return u32((x << n) | (x >> (32 - n)))

def qr(s, a, b, c, d):
    s[a] = u32(s[a] + s[b])
    s[d] = rotl(s[d] ^ s[a], 16)
    s[c] = u32(s[c] + s[d])
    s[b] = rotl(s[b] ^ s[c], 12)
    s[a] = u32(s[a] + s[b])
    s[d] = rotl(s[d] ^ s[a], 8)
    s[c] = u32(s[c] + s[d])
    s[b] = rotl(s[b] ^ s[c], 7)

def chacha(st_arr, r):
    w = st_arr[:]
    i = 0
    while i < r:
        qr(w, 0, 4, 8, 12)
        qr(w, 1, 5, 9, 13)
        qr(w, 2, 6, 10, 14)
        qr(w, 3, 7, 11, 15)
        i += 1
        if i >= r:
            break
        qr(w, 0, 5, 10, 15)
        qr(w, 1, 6, 11, 12)
        qr(w, 2, 7, 12, 13)
        qr(w, 3, 4, 13, 14)
        i += 1
    for j in range(16):
        w[j] = u32(w[j] + st_arr[j])
    return w

def bump(s):
    s[12] = u32(s[12] + 1)

def rand():
    global kt, st
    e = chacha(kt, 8)
    t = e[st]
    r = (e[st + 8] & 0xFFFFFFF0) >> 11
    if st == 7:
        bump(kt)
        st = 0
    else:
        st += 1
    return (t + 4294967296 * r) / (2 ** 53)

def nb(v):
    if v < 255 * 255:
        return [(v >> 8) & 0xFF, v & 0xFF]
    return [(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF]

def be_int(s):
    b = s.encode()[:4]
    a = 0
    for x in b:
        a = (a << 8) | x
    return a & 0xFFFFFFFF

def enc_cha(kw, r, by):
    nf = len(by) // 4
    lo = len(by) % 4
    w = [0] * ((len(by) + 3) // 4)
    
    for i in range(nf):
        j = 4 * i
        w[i] = by[j] | (by[j + 1] << 8) | (by[j + 2] << 16) | (by[j + 3] << 24)
    
    if lo:
        v = 0
        b = 4 * nf
        for c in range(lo):
            v |= by[b + c] << (8 * c)
        w[nf] = v
    
    o = 0
    s = kw[:]
    while o + 16 < len(w):
        sm = chacha(s, r)
        bump(s)
        for k in range(16):
            w[o + k] ^= sm[k]
        o += 16
    
    rm = len(w) - o
    sm = chacha(s, r)
    for k in range(rm):
        w[o + k] ^= sm[k]
    
    for i in range(nf):
        x = w[i]
        j = 4 * i
        by[j] = x & 0xFF
        by[j + 1] = (x >> 8) & 0xFF
        by[j + 2] = (x >> 16) & 0xFF
        by[j + 3] = (x >> 24) & 0xFF
    
    if lo:
        x = w[nf]
        b = 4 * nf
        for c in range(lo):
            by[b + c] = (x >> (8 * c)) & 0xFF

def ab22(k12, r, s):
    st_arr = ot + k12
    d = [ord(ch) for ch in s]
    enc_cha(st_arr, r, d)
    return ''.join(chr(x) for x in d)

def xgnarly(q, b, ua, ec=0, v='5.1.1', ts=None):
    global kt, st
    if ts is None:
        ts = int(time.time() * 1000)
    
    kt = init_prng()
    st = aa[88]
    
    obj = {}
    obj[1] = 1
    obj[2] = ec
    obj[3] = hashlib.md5(q.encode()).hexdigest()
    obj[4] = hashlib.md5(b.encode()).hexdigest()
    obj[5] = hashlib.md5(ua.encode()).hexdigest()
    obj[6] = ts // 1000
    obj[7] = 1508145731
    obj[8] = (ts * 1000) % 2147483648
    obj[9] = v
    
    if v == '5.1.1':
        obj[10] = '1.0.0.314'
        obj[11] = 1
        v12 = 0
        for i in range(1, 12):
            val = obj[i]
            tx = val if isinstance(val, int) else be_int(val)
            v12 ^= tx
        obj[12] = v12 & 0xFFFFFFFF
    elif v != '5.1.0':
        raise ValueError(f'Unsupported version: {v}')
    
    v0 = 0
    for i in range(1, len(obj) + 1):
        if i in obj:
            val = obj[i]
            if isinstance(val, int):
                v0 ^= val
    obj[0] = v0 & 0xFFFFFFFF
    
    pl = [len(obj)]
    for k in sorted(obj.keys()):
        val = obj[k]
        pl.append(k)
        vb = nb(val) if isinstance(val, int) else list(val.encode())
        pl.extend(nb(len(vb)))
        pl.extend(vb)
    
    bs = ''.join(chr(x) for x in pl)
    kw = []
    kb = []
    ra = 0
    
    for i in range(12):
        rn = rand()
        wd = int(rn * 4294967296) & 0xFFFFFFFF
        kw.append(wd)
        ra = (ra + (wd & 15)) & 15
        kb.extend([wd & 0xFF, (wd >> 8) & 0xFF, (wd >> 16) & 0xFF, (wd >> 24) & 0xFF])
    
    rds = ra + 5
    enc = ab22(kw, rds, bs)
    
    ip = 0
    for x in kb:
        ip = (ip + x) % (len(enc) + 1)
    for ch in enc:
        ip = (ip + ord(ch)) % (len(enc) + 1)
    
    kbs = ''.join(chr(x) for x in kb)
    fs = chr(((1 << 6) ^ (1 << 3) ^ 3) & 0xFF) + enc[:ip] + kbs + enc[ip:]
    
    alph = 'u09tbS3UvgDEe6r-ZVMXzLpsAohTn7mdINQlW412GqBjfYiyk8JORCF5/xKHwacP='
    out = []
    fl = (len(fs) // 3) * 3
    
    for i in range(0, fl, 3):
        blk = (ord(fs[i]) << 16) | (ord(fs[i + 1]) << 8) | ord(fs[i + 2])
        out.extend([
            alph[(blk >> 18) & 63],
            alph[(blk >> 12) & 63],
            alph[(blk >> 6) & 63],
            alph[blk & 63]
        ])
    
    return ''.join(out)

class TikTokWebSign:
    @staticmethod
    def sign(query: str, body: str = "", user_agent: str = "Mozilla/5.0", 
             include_bogus: bool = False, version: str = "5.1.1") -> dict:
        ts = int(time.time())
        xg = xgnarly(query, body, user_agent, 0, version)
        
        result = {
            'xGnarly': xg,
            'xGorgon': xg
        }
        
        if include_bogus:
            result['xBogus'] = xbogus(query, body, user_agent, ts)
        
        return result

