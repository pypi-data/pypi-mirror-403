'''Some operations for the grid storage method to save time.'''
import hashlib
def cleanupgrid(grid):
    '''Removes all non-zero coordinates from the grid.'''
    newgrid = {}
    for x in grid:
        if grid[x] != 0:
            newgrid[x] = 1
    return newgrid
def shiftgrid(grid, dx, dy):
    '''Translate a grid by a given quantity.'''
    grid = cleanupgrid(grid)
    newgrid = {}
    for x, y in grid:
        if grid[(x, y)] != 0:
            newgrid[(x + dx, y + dy)] = 1
    return newgrid
def firstcell(grid):
    '''Find the first cell in a grid.'''
    whys = [coord[1] for coord in grid]
    topcoord = min(whys)
    exes =  [coord[0] for coord in grid if coord[1] == topcoord]
    leftcoord = min(exes)
    return (leftcoord, topcoord)
def transformgrid(grid, transformation):
    '''Apply a transformation to a grid.'''
    grid = cleanupgrid(grid)
    newgrid = {}
    transformations=['flip_x','flip_y','identity','rot_90','rot_180','rot_270','flip_xy','rcw','rccw']
    if transformation not in transformations:
        raise ValueError('Only the following transformations are supported: '+str(transformations))
    match transformation:
        case 'flip_x':
            newgrid = {(-x, y):1 for x, y in grid}
        case 'flip_y':
            newgrid = {(x, -y):1 for x, y in grid}
        case 'identity':
            newgrid = {(x, y):1 for x, y in grid}
        case 'rot_90':
            newgrid = {(-y, x):1 for x, y in grid}
        case 'rot_180':
            newgrid = {(-x, -y):1 for x, y in grid}
        case 'rot_270':
            newgrid = {(y, -x):1 for x, y in grid}
        case 'flip_xy':
            newgrid = {(-x, -y):1 for x, y in grid}
        case 'rcw':
            newgrid = {(-y, x):1 for x, y in grid}
        case 'rccw':
            newgrid = {(y, -x):1 for x, y in grid}
    return newgrid
def getbbox(grid):
    '''Returns the bounding box of a grid in the form [x, y, dx, dy].'''
    grid = cleanupgrid(grid)
    if len(grid) == 0:
        #Empty patterns do not have a proper bounding box.
        return None
    exes = [c[0] for c in grid]
    whys = [c[1] for c in grid]

    x = min(exes)
    y = min(whys)
    dx = max(exes) - x + 1
    dy = max(whys) - y + 1
    return [x, y, dx, dy]
def sha1(instring):
    '''Return an integer representation of the SHA-1 hash of a string.'''
    hashed = hashlib.sha1(instring.encode('utf-8')).digest()
    totalint = 0
    for x in range(20):
        totalint += (256**x) * hashed[x]
    return totalint
def defaultshiftgrid(grid):
    '''Move a grid so that all coordinates are non-negative.'''
    grid = cleanupgrid(grid)
    bbox = getbbox(grid)
    return shiftgrid(grid, -bbox[0], -bbox[1])
def calcdigest(grid):
    '''Returns a digest of a grid, dependent on rotation and reflection but not absolute position.'''
    grid = defaultshiftgrid(grid)
    total = 0
    for x in grid:
        total += sha1(str(x))
    return total
def calcoctodigest(grid):
    '''Returns a digest of a grid, independent of rotation, reflection, and position.'''
    total = 0
    transformgrided = [grid, transformgrid(grid, 'rot_90'), transformgrid(grid, 'rot_180'), transformgrid(grid, 'rot_270')]
    transformgrided += [transformgrid(transformgrid(grid, 'flip_x'), 'rot_90'), transformgrid(transformgrid(grid, 'flip_x'), 'rot_180'), transformgrid(transformgrid(grid, 'flip_x'), 'rot_270'), transformgrid(transformgrid(grid, 'flip_x'), 'identity')]
    for x in transformgrided:
        total += calcdigest(x)
    return total
def applyop(grid1, grid2, operation):
    '''Applies an operation to two grids.'''
    grid1 = cleanupgrid(grid1)
    grid2 = cleanupgrid(grid2)
    operation = operation.lower()
    newgrid = {}
    set1 = set(grid1)
    set2 = set(grid2)
    match operation:
        case 'add':
            set3 = set1 + set2
            newgrid = {x:1 for x in set3}
        case 'sub':
            set3 = set1 - set2
            newgrid = {x:1 for x in set3}
        case 'xor':
            set3 = (set1 - set2) + (set2 - set1)
            newgrid = {x:1 for x in set3}
    return newgrid
def getcell(grid, tupleused):
    '''Gets the value of a cell.'''
    if tupleused in grid:
        return 1
    return 0
def getgridapgcode(grid):
    '''Finds the apgcode of a grid.'''
    #Documentation of apgcode format can be found at:
    #https://conwaylife.com/wiki/Apgcode
    #To my future self:
    #This function is a mess, but if all else fails,
    #Check apgsearch Py3 code to understand how it works.
    characters = '0123456789abcdefghijklmnopqrstuvwxyz'
    grid = cleanupgrid(grid)
    grid = defaultshiftgrid(grid)
    #Empty grids have no live cells:
    if len(grid) == 0:
        return '0'
    #Get the bounding box of the pattern:
    bbox = getbbox(grid)
    x, y, dx, dy = bbox[0], bbox[1], bbox[2], bbox[3]
    apgcode = ''
    for w in range((dy - 1)//5 + 1):
        if w != 0:
            apgcode += 'z'
        for l in range(dx):
            val = 0
            for h in range(5):
                val += ((2**h) * getcell(grid, (x + l, y + 5 * w + h)))
            apgcode += characters[val]
    #Remove zeroes from the end of lines:
    while apgcode.count('0z') > 0:
        apgcode = apgcode.replace('0z', 'z')
    #Use the format's compression of zeroes:
    #w corresponds to 00
    #x corresponds to 000
    #y0 through yz correspond to 4 through 39 zeroes, respectively.
    for a in range(39, 3, -1):
        apgcode = apgcode.replace('0' * a, 'y' + characters[a-4])
    apgcode = apgcode.replace('000', 'x')
    apgcode = apgcode.replace('00', 'w')
    forbiddenend = ['w', 'x', 'z', '0', 'y']
    forbiddenend += [n + '0' for n in forbiddenend]
    forbiddenend += ['y' + a for a in characters]
    forbiddenbeforez = ['x']
    if len(apgcode) > 0:
        while (apgcode[-1] in forbiddenend or apgcode[-2:-1] in forbiddenend):
            apgcode = apgcode[:-1]
    for z in forbiddenbeforez:
        while apgcode.count(z + 'z') > 0:
            apgcode = apgcode.replace(z + 'z', 'z')
    return apgcode
def apgcodetogrid(apgcode):
    '''Converts an apgcode to a grid.'''
    xpos = 0
    ypos = 0
    readpos = 0
    grid = {}
    characters = '0123456789abcdefghijklmnopqrstuvwxyz'
    apgcode = apgcode[apgcode.find('_')+1:]
    #Convert special characters to zeroes:
    for x in range(35, -1, -1):
        apgcode = apgcode.replace('y' + characters[x], '0' * (x + 4))
    apgcode = apgcode.replace('x', '000')
    apgcode = apgcode.replace('w', '00')
    print(apgcode)
    #Go through and convert the apgcode into a grid:
    while readpos < len(apgcode):
        character = apgcode[readpos]
        try:
            value = characters.find(character)
        except:
            raise ValueError('Illegal character in apgcode: '+character)
        if 0 <= value < 32:
            #We have a character denoting content.
            for x in range(5):
                if (value//(2**x))%2 == 1:
                    grid[(xpos, ypos + x)] = 1
            xpos += 1
        elif value == 35:
            #z denotes the next 5-row segment.
            xpos = 0
            ypos += 5
        readpos += 1
    return grid
def getorientations(grid):
    '''Return all 8 transformations of a grid.'''
    transformed = [grid, transformgrid(grid, 'rot_90'), transformgrid(grid, 'rot_180'), transformgrid(grid, 'rot_270')]
    transformed += [transformgrid(transformgrid(grid, 'flip_x'), 'rot_90'), transformgrid(transformgrid(grid, 'flip_x'), 'rot_180'), transformgrid(transformgrid(grid, 'flip_x'), 'rot_270'), transformgrid(transformgrid(grid, 'flip_x'), 'identity')]
    return transformed
def compareapgcode(code1, code2):
    '''Compares two apgcodes, prioritising length first and using alphabetical order for tie-breaking.'''
    if code1 == code2:
        return code1
    if len(code1) < len(code2):
        return code1
    if len(code2) < len(code1):
        return code2
    if code1 < code2:
        return code1
    if code1 > code2:
        return code2
    #This bit should be unreachable:
    return code1
def identifytype(data):
    '''Determines whether pattern data is a grid, apgcode, or RLE.'''
    if type(data) == type({}):
        return 'grid'
    if type(data) != type('string'):
        raise TypeError('Class \'Pattern\' only accepts strings or dictionaries as data, not '+str(type(data)))
    if data.count('_') == 0 or len(data) == 0 or not data.startswith('x'):
        return 'rle'
    #Catch out rle-exclusive characters:
    rle_only = ['!', '$', '#']
    for x in rle_only:
        if x in data:
            return 'rle'
    if data.replace('_', '').isalnum():
        return 'apgcode'
    return 'rle' #The RLE parser has better error handling logic, so it is the default.
        
