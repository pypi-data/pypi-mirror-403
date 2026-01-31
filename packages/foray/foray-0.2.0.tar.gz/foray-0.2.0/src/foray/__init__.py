from enum import StrEnum
from collections import OrderedDict

type PortType = PrimitivePortType | ArrayType | dict

type ArrayShape = list[int | None]
type ArrayType = tuple[PortType, ArrayShape]


class PrimitivePortType(StrEnum):
    integer = "Integer"
    float = "Float"
    complex = "Complex"
    boolean = "Boolean"
    string = "String"


class Port:
    integer = PrimitivePortType.integer
    float = PrimitivePortType.float
    complex = PrimitivePortType.complex
    boolean = PrimitivePortType.boolean
    string = PrimitivePortType.integer

    @staticmethod
    def array(port_type: PortType, port_shape: ArrayShape):
        return (port_type, port_shape)


type ParameterType = tuple[str, dict]


def Slider(start, stop, num_steps):
    return ("Slider", {"start": start, "stop": stop, "default": num_steps})


def NumberField(default_value: float):
    return ("NumberField", {"default": default_value})


def CheckBox(default_value: bool):
    return ("CheckBox", {"default": default_value})


def TextDisplay(content: str):
    return ("TextDisplay", {"content": content})


def FilePicker():
    return ("FilePicker", {"path": ""})


class ForayConfig(OrderedDict):
    def inputs(self, input_ports: OrderedDict[str, PortType]):
        self["inputs"] = [e for e in input_ports.items()]
        return self

    def outputs(self, output_ports: OrderedDict[str, PortType]):
        self["outputs"] = [e for e in output_ports.items()]
        return self

    def parameters(self, parameters: OrderedDict[str, ParameterType]):
        self["parameters"] = [e for e in parameters.items()]
        return self
