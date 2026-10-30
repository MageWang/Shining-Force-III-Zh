"""Context Huffman and 16-bit text-bank codec."""
import collections
import heapq
import struct
BASE = 0x200000

def u32(data, pos):
    return struct.unpack_from('>I', data, pos)[0]

def parse_tree(data, symbols, structure):
    bits = iter((b >> shift) & 1 for b in data[structure:] for shift in range(7, -1, -1))
    leaves = iter(data[symbols:])
    codes = {}
    def visit(code=''):
        if next(bits):
            value = next(leaves)
            codes[value] = code
            return value
        return (visit(code+'0'), visit(code+'1'))
    return visit(), codes

def read_words(data):
    table=u32(data,24)-BASE
    trees=[]
    for context in range(256):
        a,b=u32(data,table+context*8),u32(data,table+context*8+4)
        trees.append(parse_tree(data,a-BASE,b-BASE)[0] if a and b else None)
    pointers=u32(data,36)-BASE
    pages=[u32(data,i)-BASE for i in range(pointers,len(data),4)]
    output=[]
    for page,start in enumerate(pages):
        end=pages[page+1] if page+1<len(pages) else pointers
        pos=start
        for line in range(256):
            if pos>=end or not data[pos]: break
            blob=data[pos+1:pos+1+data[pos]]
            bits=iter((b>>s)&1 for b in blob for s in range(7,-1,-1))
            context=0;words=[]
            def byte():
                nonlocal context
                node=trees[context]
                if node is None: raise ValueError(f'No context {context}')
                while isinstance(node,tuple):node=node[next(bits)]
                context=node
                return node
            for _ in range(4096):
                value=(byte()<<8)|byte();words.append(value)
                if value==0:break
            else:raise ValueError('No terminator')
            output.append(dict(page=page,line=line,id=f'{page:02X}:{line:02X}',words=words))
            pos+=data[pos]+1
    return output

def huffman_tree(counts):
    heap=[];order=0
    for value,count in sorted(counts.items()):
        heapq.heappush(heap,(count,order,value));order+=1
    if not heap:return 0
    while len(heap)>1:
        a=heapq.heappop(heap);b=heapq.heappop(heap)
        heapq.heappush(heap,(a[0]+b[0],order,(a[2],b[2])));order+=1
    return heap[0][2]

def tree_bytes(tree):
    symbols=bytearray();bits=[];codes={}
    def visit(node,code=''):
        if isinstance(node,int):
            bits.append('1');symbols.append(node);codes[node]=code
        else:
            bits.append('0');visit(node[0],code+'0');visit(node[1],code+'1')
    visit(tree)
    packed=''.join(bits);packed+='0'*(-len(packed)%8)
    return bytes(symbols),bytes(int(packed[i:i+8],2) for i in range(0,len(packed),8)),codes

def build_bank(original,records,font):
    counts=[collections.Counter() for _ in range(256)]
    for record in records:
        context=0
        for value in record['words']:
            for b in (value>>8,value&255):counts[context][b]+=1;context=b
    content=bytearray(b'\0'*0x30)+font
    tree_start=len(content);pointers=[];maps=[]
    for count in counts:
        symbols,bits,codes=tree_bytes(huffman_tree(count));maps.append(codes)
        a=len(content);content.extend(symbols);b=len(content);content.extend(bits)
        pointers.append((a+BASE,b+BASE))
    while len(content)%4:content.append(0)
    table=len(content)
    for a,b in pointers:content.extend(struct.pack('>II',a,b))
    pages=[];max_record=0
    for record in records:
        if record['line']==0:pages.append(len(content)+BASE)
        context=0;bits=[]
        for value in record['words']:
            for b in (value>>8,value&255):bits.append(maps[context][b]);context=b
        packed=''.join(bits);packed+='0'*(-len(packed)%8)
        blob=bytes(int(packed[i:i+8],2) for i in range(0,len(packed),8))
        if not blob:blob=b'\0'
        if len(blob)>255:raise ValueError(f"Compressed message exceeds 255 bytes: {record['id']} = {len(blob)}")
        max_record=max(max_record,len(blob));content.append(len(blob));content.extend(blob)
    while len(content)%4:content.append(0)
    page_table=len(content)
    for value in pages:content.extend(struct.pack('>I',value))
    for offset,value in [(0,0x30+BASE),(12,tree_start+BASE),(24,table+BASE),(36,page_table+BASE)]:
        struct.pack_into('>I',content,offset,value)
    # Decode using the same context/16-bit sequence used by the game's reader.
    actual=read_words(content)
    assert [r['words'] for r in actual]==[r['words'] for r in records]
    return bytes(content),dict(font_slots=len(font)//26,bytes=len(content),max_record=max_record)
