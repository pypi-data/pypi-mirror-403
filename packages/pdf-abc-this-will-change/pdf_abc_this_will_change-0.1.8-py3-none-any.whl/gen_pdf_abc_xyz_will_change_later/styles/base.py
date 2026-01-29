from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class Style:
    def merge(self, other: 'Style') -> 'Style':
        if not isinstance(other, type(self)):
            return other
        
        new_style = type(self)()
        
        for field in self.__dataclass_fields__:
            v_self = getattr(self, field)
            v_other = getattr(other, field)
            
            if v_other is not None:
                setattr(new_style, field, v_other)
            else:
                setattr(new_style, field, v_self)
                
        return new_style
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        valid_keys = {k for k in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
