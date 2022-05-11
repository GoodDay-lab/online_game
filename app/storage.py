
from matplotlib.pyplot import table


class User:
    data = {
        'uid': None,
        'session_id': None,
    }


class Storage:
    def __init__(self) -> None:
        self.tables = {}
    
    def add_table(self, tablename, template):
        if tablename in self.tables:
            raise ValueError("There's one table with similar name")
        
        self.tables[tablename] = {
            'units': [],
            'template': template
        }
        return 
    
    def add_unit(self, tablename, unit):
        if tablename not in self.tables:
            raise ValueError("There's not table name %s" % tablename)
        
        table = self.tables[tablename]
        temp = table['template']
        for key in temp:
            if (key not in unit) or (type(unit[key]) != temp[key]):
                raise ValueError("Bad type or missing key")
        table['units'].append(unit)
    
    def get_unit(self, tablename, **data):
        if tablename not in self.tables:
            raise ValueError("There's not table name %s" % tablename)
        
        table = self.tables[tablename]
        for unit in table['units']:
            if all(unit[key] == data[key] for key in data):
                return unit
    
    def remove_unit(self, tablename, **data):
        if tablename not in self.tables:
            raise ValueError("There's not table name %s" % tablename)
        
        table = self.tables[tablename]
        target = None
        for i, unit in enumerate(table['units']):
            if all(key in unit and unit[key] == data[key] for key in data):
                target = i
                break
        del table['units'][target]
    
    def get_units(self, tablename):
        if tablename not in self.tables:
            raise ValueError("There's not table name %s" % tablename)

        return self.tables[tablename]['units']
    
    def update_unit(self, tablename, control_data, relevant_data):
        if tablename not in self.tables:
            raise ValueError("There's not table name %s" % tablename)
        
        for i, unit in enumerate(self.tables[tablename]['units']):
            if all(unit[key] == control_data[key]
                   for key in control_data):
                for key in relevant_data:
                    if type(relevant_data[key]) == self.tables[tablename]['template'][key]:
                        self.tables[tablename]['units'][i][key] = relevant_data[key]
            
