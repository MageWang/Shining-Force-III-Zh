"""Canonical source controls and atomic control arguments."""
def canonical(raw):
    values=list(raw);parts=['<00>'];i=1
    while i<len(values):
        value=values[i];i+=1
        if value in (8,9,17):
            parts.extend((f'<{value:02X}>',f'<{values[i]:02X}>'));i+=1
        else:parts.append(chr(value) if 32<=value<127 else f'<{value:02X}>')
    return ''.join(parts)
