'''The code for the lifetree and Pattern classes, which are the highest level components.'''
#Importing modules:
import copy
import math
import os
import urllib.request
import hashlib
#Other project modules:
try:
    from .hensel import RuleHandler
except ImportError:
    from hensel import RuleHandler
try:
    from .gridops import *
except ImportError:
    from gridops import *
#A few global variables:
CATAGOLUE_URL = 'https://catagolue.hatsya.com'
class Lifetree:
    '''Handles and simulates patterns.'''
    def __init__(self, rule='b3s23'):
        self.rulehandler = RuleHandler()
        self.rule = self.rulehandler.canoniserule(rule)
        self.conditionset = self.rulehandler.makeconditionset(self.rule)
    def getneighbours(self, grid):
        '''For each cell with at least one live neighbour, get a 9-bit integer.'''
        neighbours = {}
        for x in grid:
            xcor, ycor = x[0], x[1]
            for a in range(3):
                for b in range(3):
                    coord = (xcor + a - 1, ycor + b - 1)
                    if coord not in neighbours:
                        neighbours[coord] = 0
                    neighbours[coord] += 2**(8 - 3 * b - a)
        return neighbours
    def advanceone(self, grid):
        '''Advance a grid of cells by one generation.'''
        neighbours = self.getneighbours(grid)
        newgrid = {}
        for x in neighbours:
            if neighbours[x] in self.conditionset:
                newgrid[x] = 1
        return newgrid
    def advance(self, grid, gens):
        '''Advance a grid a specific number of generations.'''
        for _ in range(gens):
            grid = self.advanceone(grid)
        return grid
    def rle_to_grid(self, rle):
        '''Converts an RLE to a dictionary format.'''
        x = 0
        y = 0
        grid = {}
        position = -1
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        cstring = ''
        isnum = False
        while position + 1 < len(rle):
            position += 1
            if not isnum:
                if rle[position] == '#' or rle[position] == 'x':
                    while rle[position] != '\n' and position < len(rle) - 1:
                        position += 1
                    continue
                if rle[position] in digits:
                    isnum = True
                    cstring = rle[position]
                else:
                    operator = rle[position]
                    if operator == '\n':
                        continue
                    if cstring != '':
                        try:
                            integer = int(cstring)
                        except:
                            raise Warning('RLE is incorrectly formatted, defaulting to empty pattern...')
                            print(cstring)
                            return {}
                    else:
                        integer = 1
                    match operator:
                        case 'o':
                            for n in range(integer):
                                grid[(x+n, y)] = 1
                            x += integer
                        case 'b':
                            x += integer
                        case '$':
                            x = 0
                            y += integer
                        case '!':
                            break
                    cstring = ''
            else:
                if rle[position] not in digits:
                    isnum = False
                    position -= 1
                else:
                    if rle[position] != '\n':
                        cstring += rle[position]
        return grid
    def grid_to_rle(self, grid, bbox):
        '''Converts a grid to the RLE of a pattern.'''
        rows = {}
        for x, y in grid:
            if y not in rows:
                rows[y] = []
            rows[y].append(x)
        for x in rows:
            rows[x] = sorted(rows[x])
        rows = dict(sorted(rows.items()))
        rle = 'x = '+str(bbox[2])+', y = '+str(bbox[3])+', rule = '+self.rule.replace('b', 'B').replace('s', '/S')+'\n'
        for x in range(bbox[1], bbox[1] + bbox[3]):
            if x not in rows:
                rle += '$'
                continue
            for y in range(bbox[0], bbox[0] + bbox[2]):
                if y in rows[x]:
                    rle += 'o'
                else:
                    rle += 'b'
            rle += '$'
        rle = rle[:-1]
        rle += '!'
        #Compress the RLE:
        operators = ['o', 'b', '$']
        for x in operators:
            longestchain = 1
            while rle.count(x * (longestchain+1)) > 0:
                longestchain += 1
            if longestchain >= 2:
                for n in range(longestchain, 2, -1):
                    rle = rle.replace(x * n, str(n)+x)
        return rle
    def hashsoup(self, instring, sym):
        '''Generates a soup based on the instring, returning a Pattern.'''
        #I borrowed this function from apgsearch Py3 - see the repo (https://github.com/PKTwentyTwo/apgsearch-Py3) for the credits for this function.
        if sym[0] in ['G', 'H'] and 'stdin' not in sym.lower() and len(sym) > 1:
            sym = sym[0].replace('G', 'C').replace('H', 'D') + sym[1:]
            #Adaptation to account for GPU symmetries.
        s = hashlib.sha256(instring.encode('utf-8')).digest()
        thesoup = []
        if sym in ['D2_x', 'D8_1', 'D8_4']:
            d = 1
        elif sym in ['D4_x1', 'D4_x4']:
            d = 2
        else:
            d = 0
        for j in range(32):
            t = s[j]
            for k in range(8):
                if sym in ['8x32']:
                    x = k + 8*(j % 4)
                    y = int(j / 4)
                elif sym in ['4x64']:  
                    x = k + 8*(j % 8)
                    y = int(j / 8)
                elif sym in ['2x128']:
                    x = k + 8*(j % 16)
                    y = int(j / 16)
                elif sym in ['1x256']:
                    x = k + 8*(j % 32)
                    y = int(j / 32)
                else:
                    x = k + 8*(j % 2)
                    y = int(j / 2)
                if (t & (1 << (7 - k))):
                    if (d == 0) | (x >= y):
                        thesoup.append(x)
                        thesoup.append(y)
                    elif sym in ['D4_x1']:
                        thesoup.append(y)
                        thesoup.append(-x)
                    elif sym in ['D4_x4']:
                        thesoup.append(y)
                        thesoup.append(-x-1)
                    if (sym in ['D4_x1']) & (x == y):
                        thesoup.append(y)
                        thesoup.append(-x)
                    if (sym in ['D4_x4']) & (x == y):
                        thesoup.append(y)
                        thesoup.append(-x-1)
        # Checks for diagonal symmetries:
        if (d >= 1):
            for x in range(0, len(thesoup), 2):
                thesoup.append(thesoup[x+1])
                thesoup.append(thesoup[x])
            if d == 2:
                if sym == 'D4_x1':
                    for x in range(0, len(thesoup), 2):
                        thesoup.append(-thesoup[x+1])
                        thesoup.append(-thesoup[x])
                else:
                    for x in range(0, len(thesoup), 2):
                        thesoup.append(-thesoup[x+1] - 1)
                        thesoup.append(-thesoup[x] - 1)
        # Checks for orthogonal x symmetry:
        if sym in ['D2_+1', 'D4_+1', 'D4_+2']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(thesoup[x])
                thesoup.append(-thesoup[x+1])
        elif sym in ['D2_+2', 'D4_+4']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(thesoup[x])
                thesoup.append(-thesoup[x+1] - 1)
        # Checks for orthogonal y symmetry:
        if sym in ['D4_+1']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(-thesoup[x])
                thesoup.append(thesoup[x+1])
        elif sym in ['D4_+2', 'D4_+4']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(-thesoup[x] - 1)
                thesoup.append(thesoup[x+1])
        # Checks for rotate2 symmetry:
        if sym in ['C2_1', 'C4_1', 'D8_1']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(-thesoup[x])
                thesoup.append(-thesoup[x+1])
        elif sym in ['C2_2']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(-thesoup[x])
                thesoup.append(-thesoup[x+1]-1)
        elif sym in ['C2_4', 'C4_4', 'D8_4']:
            for x in range(0, len(thesoup), 2):
                thesoup.append(-thesoup[x]-1)
                thesoup.append(-thesoup[x+1]-1)
        # Checks for rotate4 symmetry:
        if (sym in ['C4_1', 'D8_1']):
            for x in range(0, len(thesoup), 2):
                thesoup.append(thesoup[x+1])
                thesoup.append(-thesoup[x])
        elif (sym in ['C4_4', 'D8_4']):
            for x in range(0, len(thesoup), 2):
                thesoup.append(thesoup[x+1])
                thesoup.append(-thesoup[x]-1)
        thesoup2 = {}
        for x in range(len(thesoup)//2):
            thesoup2[(thesoup[2*x], thesoup[2*x+1])] = 1
        return self.pattern(thesoup2)
    def download_synth(self, apgcode):
        '''Downloads a glider synthesis from Catagolue.'''
        if self.rule != 'b3s23':
            raise ValueError('Can only download syntheses if configured for b3s23.')
        c = urllib.request.urlopen(CATAGOLUE_URL + '/textsamples/' + apgcode + '/' + 'b3s23/synthesis')
        response = c.read().decode('utf-8')
        if 'x' in response:
            return response
        return None
    def download_soups(self, apgcode, sym='C1'):
        '''Returns a list of soups producing a target object.'''
        c = urllib.request.urlopen(CATAGOLUE_URL + '/textsamples/' + apgcode + '/' + self.rule)
        response = c.read().decode('utf-8')
        soups = []
        for x in response.split('\n'):
            data = x.split('/')
            if len(data) != 2:
                continue
            symmetry, seed = data[0], data[1]
            if symmetry != sym:
                continue
            soups.append(self.hashsoup(seed, symmetry))
        return soups
    def pattern(self, data):
        '''Creates a new Pattern given an RLE string.'''
        datatype = identifytype(data)
        if datatype == 'rle':
            grid = self.rle_to_grid(data)
        elif datatype == 'apgcode':
            grid = apgcodetogrid(data)
        else:
            grid = data
        pt = Pattern(self, grid)
        return pt
class Pattern:
    '''This is the class used for manipulation of patterns.'''
    def __init__(self, lifetree, grid={}):
        '''This method should only be called by a lifetree.'''
        self.lifetree = lifetree
        self.grid = grid
    def __getitem__(self, gens):
        '''Advances a pattern a given number of generations.'''
        self2 = self.clone()
        self2.grid = self2.lifetree.advance(self.grid, gens)
        return self2
    def __call__(self, *args):
        '''Translates or transforms a pattern.'''
        if len(args) == 2:
            return self.move(args[0], args[1])
        if len(args) == 1:
            return self.transform(args[0])
        raise TypeError('Expected at most 2 arguments, received '+str(len(args))+'.')
    def __or__(self, other):
        '''Returns the OR of two patterns.'''
        if type(self) != type(other):
            raise TypeError('Can only perform logical operations with other instances of Pattern.')
        cells = applyop(self.grid, other.grid, 'add')
        return self.lifetree.pattern(cells)
    def __add__(self, other):
        '''Returns the OR of two patterns.'''
        return self.__or__(other)
    def __xor__(self, other):
        '''Returns the XOR of two patterns.'''
        if type(self) != type(other):
            raise TypeError('Can only perform logical operations with other instances of Pattern.')
        cells = applyop(self.grid, other.grid, 'xor')
        return self.lifetree.pattern(cells)
    def __sub__(self, other):
        '''Removes live cells in one pattern from the other.'''
        if type(self) != type(other):
            raise TypeError('Can only perform logical operations with other instances of Pattern.')
        cells = applyop(self.grid, other.grid, 'sub')
        return self.lifetree.pattern(cells)
    def __ixor__(self, other):
        '''Returns the XOR of two patterns.'''
        return self.__xor__(other)
    def transform(self, transformation):
        '''Transforms a pattern relative to the origin.'''
        pt2 = self.clone()
        pt2.grid = transformgrid(self.grid, transformation)
        return pt2
    def centre(self):
        '''Moves a pattern so that the bounding box is centered on the origin.'''
        bbox = self.bbox
        dx = -math.floor((bbox[0] + bbox[2])/2)
        dy = -math.floor((bbox[1] + bbox[3])/2)
        return self(dx, dy)
    def clone(self):
        '''Creates a copy of a pattern.'''
        thecopy = copy.deepcopy(self)
        thecopy.cleanup()
        return thecopy
    def cleanup(self):
        '''Cleans up the stored data of a pattern.'''
        self.grid = cleanupgrid(self.grid)
    def move(self, dx, dy):
        '''Translates a pattern by (dx, dy).'''
        self2 = self.clone()
        self2.grid = shiftgrid(self.grid, dx, dy)
        self2.cleanup()
        return self2
    def oscar(self, maxgens=1024):
        '''Finds the period of a pattern. Returns an error if it is aperiodic.'''
        inithash = self.digest
        pt = self.clone()[1]
        gens = 1
        while pt.digest != inithash:
            pt = pt[1]
            gens += 1
            if gens > maxgens:
                raise ValueError('Pattern does not become periodic within '+str(maxgens)+' generations.')
                return -1
        return gens
    def save(self, filename = 'pattern.rle'):
        '''Saves the RLE of a pattern in a file.'''
        rle = self.rle
        f = open(filename, 'w', encoding = 'utf-8')
        f.write(rle)
        f.close()
    @property
    def rle(self):
        '''The Run Length Encoding (RLE) of a pattern.'''
        self.cleanup()
        return self.lifetree.grid_to_rle(self.grid, self.bbox)
    @property
    def population(self):
        '''How many live cells a pattern has.'''
        self.cleanup()
        return len(self.grid)
    @property
    def coords(self):
        '''A list of every cell in a pattern.'''
        self.cleanup()
        thecoords = []
        for x in self.grid:
            thecoords.append(x)
        return thecoords
    @property
    def firstcell(self):
        '''The first cell of a pattern.'''
        self.grid = dict(sorted(self.grid.items()))
        count = 0
        for x in self.grid:
            count += 1
            if count == 1:
                return x
        return None
    @property
    def digest(self):
        '''A hash of the pattern (orientation dependent).'''
        return calcdigest(self.grid)
    @property
    def octodigest(self):
        '''A hash of the pattern (orientation independent).'''
        return calcoctodigest(self.grid)
    @property
    def period(self):
        '''The period of a pattern. Returns an error if aperiodic.'''
        return self.oscar()
    @property
    def displacement(self):
        '''The displacement of a periodic pattern in the form (dx, dy). Returns an error if aperiodic.'''
        period = self.period
        if self.population == 0:
            raise ValueError('Cannot calculate displacement for an empty pattern.')
        firstcella = self.firstcell
        firstcellb = self[period].firstcell
        displacement = (firstcellb[0] - firstcella[0], firstcellb[1] - firstcella[1])
        return displacement
        
    @property
    def bbox(self):
        '''The bounding box of a pattern in the form [x, y, dx, dy].'''
        cells = self.coords
        if len(cells) == 0:
            #Empty patterns do not have a proper bounding box.
            return None
        exes = [c[0] for c in cells]
        whys = [c[1] for c in cells]

        x = min(exes)
        y = min(whys)
        dx = max(exes) - x + 1
        dy = max(whys) - y + 1
        return [x, y, dx, dy]
    @property
    def components(self):
        '''A list of the connected islands in a pattern.'''
        coords = self.coords
        islands = []
        while len(coords) > 0:
            coord = coords[0]
            island = [coord]
            coords.remove(coord)
            chosencoord = 0
            while chosencoord < len(island):
                coord = island[chosencoord]
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        neighbour = (coord[0] + dx, coord[1] + dy)
                        if neighbour in coords and neighbour not in islands:
                            coords.remove(neighbour)
                            island.append(neighbour)
                chosencoord += 1
            islands.append(island)

        islands2 = []
        for x in islands:
            current_island = {}
            for y in x:
                current_island[y] = 1
            islands2.append(self.lifetree.pattern(current_island))
        return islands2
    @property
    def apgcode(self):
        '''A unique identifier for periodic patterns.'''
        print(getgridapgcode(self.grid))
        period = self.period
        print(period)
        if period == -1:
            return 'aperiodic'
        pt = self.clone()
        gridphases = []
        for x in range(period):
            gridphases.append(pt.grid)
            pt = pt[1]
        gridphases2 = []
        for x in gridphases:
            gridphases2 += getorientations(x)
        canonicalapgcode = 'Z'*10000
        for x in gridphases2:
            canonicalapgcode = compareapgcode(canonicalapgcode, getgridapgcode(x))
        if period == 1:
            prefix = 'xs' + str(self.population) + '_'
        else:
            if self.displacement != (0, 0):
                prefix = 'xq' + str(period) + '_'
            else:
                prefix = 'xp' + str(period) + '_'
        
        return prefix + canonicalapgcode
