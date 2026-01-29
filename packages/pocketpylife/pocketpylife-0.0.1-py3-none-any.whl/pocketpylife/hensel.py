'''This module contains a class, RuleHandler, for dealing with Hensel notation.'''
import copy
import re
class RuleHandler:
    '''Responsible for handling Hensel notation.'''
    def __init__(self):
        '''Only needs to set up some read-only variables.'''
        #Dictionary mapping digits to their Hensel notation letters.
        self.conditiondict = {
            '0':[''],
            '1':['c', 'e'],
            '2':['a','c','e','i','k','n'],
            '3':['a','c','e','i','j','k','n','q','r','y'],
            '4':['a','c','e','i','j','k','n','q','r','t','w','y','z'],
            '5':['a','c','e','i','j','k','n','q','r','y'],
            '6':['a','c','e','i','k','n'],
            '7':['c', 'e'],
            '8':['']
            }
    def isvalid(self, rule):
        '''Checks if a rule is valid using regex.'''
        rule = rule.lower().replace('/', '')
        return bool(re.match('b[1-8ceaiknjqrytwz-]*s[0-8ceaiknjqrytwz-]*', rule))
    def parserule(self, rule):
        '''Takes a rule and returns a list of birth and survival conditions.'''
        #I hate having to code parsers.
        if not self.isvalid(rule):
            raise ValueError('Rule does not match regex b[1-8ceaiknjqrytwz-]*s[0-8ceaiknjqrytwz-]*')
        #Convert the rule to a fixed format:
        rule = rule.lower().replace('/', '')
        conditiondict = self.conditiondict
        conditions = []
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
        cstring = ''
        birth = True
        rule = rule + '|' #Using a vertical bar to signify the end of the rulestring.
        for character in rule:
            if character in digits or character in ['b', 's', '|']:
                cstring = cstring.replace('b', '').replace('s', '')
                if cstring != '':
                    digit = cstring[0]
                    if len(cstring) == 1:
                        for x in conditiondict[cstring]:
                            if birth:
                                conditions.append('B' + cstring + x)
                            else:
                                conditions.append('S' + cstring + x)
                    else:
                        subconditions = cstring[1:]
                        if subconditions[0] == '-':
                            temp = copy.deepcopy(conditiondict[digit])
                            for x in cstring[2:]:
                                if x in temp:
                                    temp.remove(x)
                            for x in temp:
                                if birth:
                                    conditions.append('B' + digit + x)
                                else:
                                    conditions.append('S' + digit + x)
                        else:
                            temp = []
                            for x in subconditions:
                                if x in conditiondict[digit]:
                                    temp.append(x)
                            for x in temp:
                                if birth:
                                    conditions.append('B' + digit + x)
                                else:
                                    conditions.append('S' + digit + x)
                cstring = ''
            if character == 's':
                birth = False
            cstring = cstring + character
        for x in conditions:
            if conditions.count(x) > 1:
                conditions.remove(x)
        return conditions
    def tohensel(self, conditions):
        '''Takes a list of parsed conditions and turns them back into Hensel notation.'''
        conditions.sort()
        conditiondict = self.conditiondict
        newconditions = {}
        for x in conditions:
            if len(x) == 2:
                prefix = x
                suffix = ''
            else:
                prefix = x[:2]
                suffix = x[2]
            if prefix not in newconditions:
                newconditions[prefix] = []
            newconditions[prefix].append(suffix)
        rulestring = 'B'
        birth = True
        for x in newconditions:
            if x[0] == 'S' and birth:
                birth = False
                rulestring += '/S'
            num_conditions = len(newconditions[x])
            total_conditions = len(conditiondict[x[1]])
            if num_conditions == total_conditions:
                #No need for letters if the number of conditions matches the total.
                rulestring += x[1]
                continue
            if num_conditions * 2 <= total_conditions:
                #Less than or equal to half of the total conditions are present:
                rulestring += x[1]
                newconditions[x].sort()
                for n in newconditions[x]:
                    rulestring += n
                continue
            if num_conditions * 2 > total_conditions:
                #More than half of the total conditions are present.
                missing_conditions = list(set(conditiondict[x[1]]) - set(newconditions[x]))
                missing_conditions.sort()
                rulestring += x[1] + '-'
                for n in missing_conditions:
                    rulestring += n
                continue
        return rulestring
    def get_9bit(self, condition):
        '''Returns a list of 9-bit decimal numbers, used to apply INT rules.'''
        #I absolutely hated this part, but at least
        #I was able to automate it partially using
        #another Python script.
        conditions = []
        match condition:
            case 'B0':
                conditions = [0]
            case 'B1e':
                conditions = [2, 8, 32, 128]
            case 'B1c':
                conditions = [1, 4, 64, 256]
            case 'B2a':
                conditions = [3, 6, 9, 36, 72, 192, 288, 384]
            case 'B2e':
                conditions = [10, 34, 136, 160]
            case 'B2c':
                conditions = [5, 65, 260, 320]
            case 'B2i':
                conditions = [40, 130]
            case 'B2k':
                conditions = [12, 33, 66, 96, 129, 132, 258, 264]
            case 'B2n':
                conditions = [68, 257]
            case 'B3a':
                conditions = [11, 38, 200, 416]
            case 'B3c':
                conditions = [69, 261, 321, 324]
            case 'B3e':
                conditions = [42, 138, 162, 168]
            case 'B3i':
                conditions = [7, 73, 292, 448]
            case 'B3j':
                conditions = [14, 35, 74, 137, 164, 224, 290, 392]
            case 'B3k':
                conditions = [98, 140, 161, 266]
            case 'B3n':
                conditions = [13, 37, 67, 193, 262, 328, 352, 388]
            case 'B3q':
                conditions = [70, 76, 100, 196, 259, 265, 289, 385]
            case 'B3r':
                conditions = [41, 44, 104, 131, 134, 194, 296, 386]
            case 'B3y':
                conditions = [97, 133, 268, 322]
            case 'B4a':
                conditions = [15, 39, 75, 201, 294, 420, 456, 480]
            case 'B4c':
                conditions = [325]
            case 'B4e':
                conditions = [170]
            case 'B4i':
                conditions = [45, 195, 360, 390]
            case 'B4j':
                conditions = [106, 142, 163, 169, 172, 226, 298, 394]
            case 'B4k':
                conditions = [99, 141, 165, 225, 270, 330, 354, 396]
            case 'B4n':
                conditions = [71, 77, 263, 293, 329, 356, 449, 452]
            case 'B4q':
                conditions = [102, 204, 267, 417]
            case 'B4r':
                conditions = [43, 46, 139, 166, 202, 232, 418, 424]
            case 'B4t':
                conditions = [105, 135, 300, 450]
            case 'B4w':
                conditions = [94, 244, 307, 409]
            case 'B4y':
                conditions = [101, 197, 269, 323, 326, 332, 353, 389]
            case 'B4z':
                conditions = [108, 198, 297, 387]
            case 'B5a':
                conditions = [79, 295, 457, 484]
            case 'B5c':
                conditions = [171, 174, 234, 426]
            case 'B5e':
                conditions = [327, 333, 357, 453]
            case 'B5i':
                conditions = [47, 203, 422, 488]
            case 'B5j':
                conditions = [103, 205, 271, 331, 358, 421, 460, 481]
            case 'B5k':
                conditions = [229, 334, 355, 397]
            case 'B5n':
                conditions = [107, 143, 167, 233, 302, 428, 458, 482]
            case 'B5q':
                conditions = [110, 206, 230, 236, 299, 395, 419, 425]
            case 'B5r':
                conditions = [109, 199, 301, 361, 364, 391, 451, 454]
            case 'B5y':
                conditions = [173, 227, 362, 398]
            case 'B6a':
                conditions = [111, 207, 303, 423, 459, 486, 489, 492]
            case 'B6c':
                conditions = [175, 235, 430, 490]
            case 'B6e':
                conditions = [335, 359, 461, 485]
            case 'B6i':
                conditions = [365, 455]
            case 'B6k':
                conditions = [231, 237, 363, 366, 399, 429, 462, 483]
            case 'B6n':
                conditions = [238, 427]
            case 'B7c':
                conditions = [239, 431, 491, 494]
            case 'B7e':
                conditions = [367, 463, 487, 493]
            case 'B8':
                conditions = [495]
        if len(conditions) > 0:
            return conditions
        if condition[0] == 'S':
            #Since I'm not about to manually add more conditions,
            #I just add 16 to account for the central cell
            #for survival conditions.
            newcon = condition.replace('S', 'B')
            newlist = self.get_9bit(newcon)
            newlist = [x + 16 for x in newlist]
            return newlist
        return []
    def makeconditionset(self, rule):
        '''Creates the condition set used by a lifetree.'''
        numeric_conditions = []
        conditions = self.parserule(rule)
        for x in conditions:
            numeric_conditions += self.get_9bit(x)
        numeric_conditions.sort()
        return set(numeric_conditions)
    def canoniserule(self, rule):
        '''Canonises a rule to a fixed format.'''
        return self.tohensel(self.parserule(rule)).lower().replace('/', '')
