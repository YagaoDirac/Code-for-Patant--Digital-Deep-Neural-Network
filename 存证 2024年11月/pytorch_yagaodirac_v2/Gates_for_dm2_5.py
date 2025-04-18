from typing import List, Tuple, Any
import torch

import sys
ori_path = sys.path[0]
index = ori_path.rfind("\\")
upper_folder = ori_path[:index]
sys.path.append(upper_folder)
del ori_path
del index
del upper_folder

#from pytorch_yagaodirac_v2.Digital_mapper_v2_5 import DigitalMapper_v2_5

#笔记。
#这个版本适配的是目标回传（target/label/answer propagation）的digital mapper，具体版本是2.4和2.5，我忘了2.3是不是了。
#反正只有2.5是通过了最后那个测试的。所以这个门层现在只适配2.5.
#门层本身的原理和选线器层很类似，能清晰的找到回传通路的，直接传答案回去，不能清晰的找到的，乘以alpha缩小，但是方向依然是队的。
#考虑到xor的特殊性，暂时不写。
#这个版本在11月的答复补正当中不最终确定，在后续的主动补正里面再具体描述。
#门只有，非，且，或，3个。暂时不做且非和或非。所有多输入门只做2输入。

#基本原理是，不用之前的数学公式的版本了，那个适配的是误差回传（error/backward propagation)。
#原理是用类似池层的手感，但是不是池，而是完全自己写的一个结构。
#之前那个版本，且门是要通过一些计算，然后过二值化层。这个版本根本就没有二值化那些事情了，forward里面是纯数字化的，离散的。
#反向传播的部分依然是我最喜欢的“稠密”手感。


'''
def calculate_fake_alpha(raw:float)->float:
    r''formula is: 
    -1......0......1
    -1......0..a   (a means alpha)
    but because the result will go through a gramo, I can save some calculation.
    -k.........0...k*a
    a*k+k == 2
    (a+1)k == 2
    k == 2/(a+1)
    what I need is the distance between 1 and k*a
    -k.........0...k*a???1
    then, 1-a*k == k-1 == 2/(a+1)-1 == (1-a)/(1+a)
    ''
    return (1.-raw)/(1+raw)
'''



class NOT_Gate_Function(torch.autograd.Function):
    r'''
    forward input list:
    >>> x = args[0]# shape must be [batch, in_features]
    backward input list:
    >>> g_in #shape of g_in must be [batch, out_features]
    '''
    @staticmethod
    def forward(ctx: Any, *args: Any, **kwargs: Any)->Any:
        input_b_i:torch.Tensor = args[0]# shape must be [batch, in_features]
        
        if input_b_i.shape.__len__() !=2:
            raise Exception()
        
        temp1:torch.Tensor = input.lt(0.)
        temp4 = temp1*2.-1
        output = temp4.to(input_b_i.dtype)
        output.requires_grad_(input_b_i.requires_grad)
        
        input_requires_grad = torch.tensor([input_b_i.requires_grad], device=input_b_i.device)
        ctx.save_for_backward(input_requires_grad)
        return output

    @staticmethod
    def backward(ctx, g_in_b_o):
        #shape of g_in must be [batch, out_features]
        input_requires_grad:torch.Tensor
        (input_requires_grad) = ctx.saved_tensors
        
        grad_for_x_b_i:Tuple[torch.Tensor|None] = None
        if input_requires_grad:
            grad_for_x_b_i = g_in_b_o*-1.
            pass
        return grad_for_x_b_i, None

    pass  # class

if 'basic test' and False:
    input = torch.tensor([[1.,1,-1,-1]], requires_grad=True)
    pred = NOT_Gate_Function.apply(input)
    print(pred, "pred")
    target = torch.tensor([[1.,-1,1,-1]], requires_grad=True)
    pred.backward(target)
    print(input.grad, "input.grad")
    pass


class NOT_Gate(torch.nn.Module):
                 #first_big_number:float = 3., 
    def __init__(self, device=None, dtype=None) -> None:
        factory_kwargs = {'device': device, 'dtype': dtype}
        super().__init__()
        pass
    
    def ______a(a):
        '''
    def accepts_non_standard_range(self)->bool:
        return False
    def outputs_standard_range(self)->bool:
        return True
    def outputs_non_standard_range(self)->bool:
        return not self.outputs_standard_range()
        '''
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        # If you know how pytorch works, you can comment this checking out.
        # if not input.requires_grad:
        #     raise Exception("Set x.requires_grad to True. If you know what you are doing, you can comment this line.")
        if len(input.shape)!=2:
            raise Exception("Gates layers only accept rank-2 tensor. The shape should be[batch, gate_count * input_count]. If you have 5 data in a batch, you need 3 gates and each is AND2(which needs 2 inputs), the shape should be (5,6).")
        
        result = NOT_Gate_Function.apply(input)
        return result
        #end of function
    pass

if 'basic test' and False:
    input = torch.tensor([[1.,1,-1,-1]], requires_grad=True)
    layer = NOT_Gate()
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[1.,-1,1,-1]], requires_grad=True)
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    pass




class AND_Gate_Function(torch.autograd.Function):
    r'''I assumed there is always a gramo before this, so the g_out only cares direction, not the length.
        
    forward input list:
    >>> x = args[0]# shape must be [batch, in_features]
    >>> alpha = args[1]
    backward input list:
    >>> g_in #shape of g_in must be [batch, out_features]
    '''
    @staticmethod
    def forward(ctx: Any, *args: Any, **kwargs: Any)->Any:
        input_b_i:torch.Tensor = args[0]# shape must be [batch, in_features]
        alpha_s:torch.Tensor = args[1]# something for backward
        
        if input_b_i.shape.__len__() !=2:
            raise Exception()
        if input_b_i.shape[-1] %2!=0:
            raise Exception()
        
        gate_count = input_b_i.shape[-1]//2
        temp1:torch.Tensor = input[:,:gate_count].gt(0.)
        temp2 = input[:,gate_count:].gt(0.)
        temp3 = temp1.logical_and(temp2)
        temp4 = temp3*2.-1
        output = temp4.to(input_b_i.dtype)
        output.requires_grad_(input_b_i.requires_grad)
        
        input_requires_grad = torch.tensor([input_b_i.requires_grad], device=input_b_i.device)
        ctx.save_for_backward(input_requires_grad, alpha_s)
        return output

    @staticmethod
    def backward(ctx, g_in_b_o):
        #shape of g_in must be [batch, out_features]
        input_requires_grad:torch.Tensor
        alpha_s:torch.Tensor
        (input_requires_grad, alpha_s) = ctx.saved_tensors
        
        grad_for_x_b_i:Tuple[torch.Tensor|None] = None
        if input_requires_grad:
            flag_g_in_is_True__b_o:torch.Tensor = g_in_b_o.gt(0.)
            part1_b_o = flag_g_in_is_True__b_o*g_in_b_o
            part2_b_o = flag_g_in_is_True__b_o.logical_not()*-1.*alpha_s
            grad_for_x__before_repeat__b_o:torch.Tensor = part1_b_o + part2_b_o
            grad_for_x_b_i = grad_for_x__before_repeat__b_o.reshape([grad_for_x__before_repeat__b_o.shape[0],1,grad_for_x__before_repeat__b_o.shape[1]]).repeat([1,2,1]).reshape([grad_for_x__before_repeat__b_o.shape[0],-1])
            #old code
            #g_in_abs_b_o = g_in_b_o.abs()
            #grad_for_x_b_i = g_in_b_o - g_in_abs_b_o*fake_alpha_s
            pass
        return grad_for_x_b_i, None

    pass  # class

if 'basic test' and False:
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    alpha = torch.tensor([0.1])
    pred = AND_Gate_Function.apply(input,alpha)
    print(pred, "pred")
    target = torch.tensor([[1.,1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    alpha = torch.tensor([0.1])
    pred = AND_Gate_Function.apply(input,alpha)
    print(pred, "pred")
    target = torch.tensor([[-1.,-1,-1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    alpha = torch.tensor([0.1])
    pred = AND_Gate_Function.apply(input,alpha)
    print(pred, "pred")
    target = torch.tensor([[1.,-1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    pass


class AND_Gate(torch.nn.Module):
                 #first_big_number:float = 3., 
    def __init__(self, alpha:float, debug__allows_any_alpha = False, \
                #output_mode_0_is_self_only__1_is_both__2_is_opposite_only:int=0, \
                device=None, dtype=None) -> None:
        factory_kwargs = {'device': device, 'dtype': dtype}
        super().__init__()
        '''
        if not output_mode_0_is_self_only__1_is_both__2_is_opposite_only in[0,1,2]:
            raise Exception("Param:output_mode_0_is_self_only__1_is_both__2_is_opposite_only can only be 0, 1 or 2.")
        self.output_mode_0_is_self_only__1_is_both__2_is_opposite_only = output_mode_0_is_self_only__1_is_both__2_is_opposite_only
        
        if input_per_gate<2:
            raise Exception("Param:input_per_gate should >=2.")
        self.input_per_gate = input_per_gate
        # self.input_per_gate = torch.nn.Parameter(torch.tensor([input_per_gate]), requires_grad=False)
        # self.input_per_gate.requires_grad_(False)
        '''
        
        if not debug__allows_any_alpha:
            if alpha<=0. or alpha>1.:
                raise Exception("if you know what you are doing, set debug__allows_any_alpha=True.")
            pass
        
        self.alpha = torch.nn.Parameter(torch.tensor([alpha]), requires_grad=False)
        pass
    
    def ______a(a):
        '''
    def accepts_non_standard_range(self)->bool:
        return False
    def outputs_standard_range(self)->bool:
        return True
    def outputs_non_standard_range(self)->bool:
        return not self.outputs_standard_range()
        '''
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x:torch.Tensor
        # If you know how pytorch works, you can comment this checking out.
        # if not input.requires_grad:
        #     raise Exception("Set x.requires_grad to True. If you know what you are doing, you can comment this line.")
        if len(input.shape)!=2:
            raise Exception("Gates layers only accept rank-2 tensor. The shape should be[batch, gate_count * input_count]. If you have 5 data in a batch, you need 3 gates and each is AND2(which needs 2 inputs), the shape should be (5,6).")
        
        result = AND_Gate_Function.apply(input, self.alpha)
        return result
        #end of function
    pass

if 'basic test' and False:
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    layer = AND_Gate(0.1)
    print(layer.alpha.data, "alpha")
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[1.,1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    layer = AND_Gate(0.1)
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[-1.,-1,-1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    layer = AND_Gate(0.1)
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[1.,-1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    pass




class OR_Gate_Function(torch.autograd.Function):
    r'''I assumed there is always a gramo before this, so the g_out only cares direction, not the length.
        
    forward input list:
    >>> x = args[0]# shape must be [batch, in_features]
    >>> alpha = args[1]
    backward input list:
    >>> g_in #shape of g_in must be [batch, out_features]
    '''
    @staticmethod
    def forward(ctx: Any, *args: Any, **kwargs: Any)->Any:
        input_b_i:torch.Tensor = args[0]# shape must be [batch, in_features]
        alpha_s:torch.Tensor = args[1]# something for backward
        
        if input_b_i.shape.__len__() !=2:
            raise Exception()
        if input_b_i.shape[-1] %2!=0:
            raise Exception()
        
        gate_count = input_b_i.shape[-1]//2
        temp1:torch.Tensor = input[:,:gate_count].gt(0.)
        temp2 = input[:,gate_count:].gt(0.)
        temp3 = temp1.logical_or(temp2)
        temp4 = temp3*2.-1
        output = temp4.to(input_b_i.dtype)
        output.requires_grad_(input_b_i.requires_grad)
        
        input_requires_grad = torch.tensor([input_b_i.requires_grad], device=input_b_i.device)
        ctx.save_for_backward(input_requires_grad, alpha_s)
        return output

    @staticmethod
    def backward(ctx, g_in_b_o):
        #shape of g_in must be [batch, out_features]
        input_requires_grad:torch.Tensor
        alpha_s:torch.Tensor
        (input_requires_grad, alpha_s) = ctx.saved_tensors
        
        grad_for_x_b_i:Tuple[torch.Tensor|None] = None
        if input_requires_grad:
            flag_g_in_is_True__b_o:torch.Tensor = g_in_b_o.gt(0.)
            part1_b_o = flag_g_in_is_True__b_o*g_in_b_o*alpha_s
            part2_b_o = flag_g_in_is_True__b_o.logical_not()*-1.
            grad_for_x__before_repeat__b_o:torch.Tensor = part1_b_o + part2_b_o
            grad_for_x_b_i = grad_for_x__before_repeat__b_o.reshape([grad_for_x__before_repeat__b_o.shape[0],1,grad_for_x__before_repeat__b_o.shape[1]]).repeat([1,2,1]).reshape([grad_for_x__before_repeat__b_o.shape[0],-1])
            #old code
            #g_in_abs_b_o = g_in_b_o.abs()
            #grad_for_x_b_i = g_in_b_o - g_in_abs_b_o*fake_alpha_s
            pass
        return grad_for_x_b_i, None

    pass  # class

if 'basic test' and False:
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    alpha = torch.tensor([0.1])
    pred = OR_Gate_Function.apply(input,alpha)
    print(pred, "pred")
    target = torch.tensor([[1.,1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    alpha = torch.tensor([0.1])
    pred = OR_Gate_Function.apply(input,alpha)
    print(pred, "pred")
    target = torch.tensor([[-1.,-1,-1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    alpha = torch.tensor([0.1])
    pred = OR_Gate_Function.apply(input,alpha)
    print(pred, "pred")
    target = torch.tensor([[1.,-1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    pass


class OR_Gate(torch.nn.Module):
                 #first_big_number:float = 3., 
    def __init__(self, alpha:float, debug__allows_any_alpha = False, \
                #output_mode_0_is_self_only__1_is_both__2_is_opposite_only:int=0, \
                device=None, dtype=None) -> None:
        factory_kwargs = {'device': device, 'dtype': dtype}
        super().__init__()
        '''
        if not output_mode_0_is_self_only__1_is_both__2_is_opposite_only in[0,1,2]:
            raise Exception("Param:output_mode_0_is_self_only__1_is_both__2_is_opposite_only can only be 0, 1 or 2.")
        self.output_mode_0_is_self_only__1_is_both__2_is_opposite_only = output_mode_0_is_self_only__1_is_both__2_is_opposite_only
        
        if input_per_gate<2:
            raise Exception("Param:input_per_gate should >=2.")
        self.input_per_gate = input_per_gate
        # self.input_per_gate = torch.nn.Parameter(torch.tensor([input_per_gate]), requires_grad=False)
        # self.input_per_gate.requires_grad_(False)
        '''
        
        if not debug__allows_any_alpha:
            if alpha<=0. or alpha>1.:
                raise Exception("if you know what you are doing, set debug__allows_any_alpha=True.")
            pass
        
        self.alpha = torch.nn.Parameter(torch.tensor([alpha]), requires_grad=False)
        pass
    
    def ______a(a):
        '''
    def accepts_non_standard_range(self)->bool:
        return False
    def outputs_standard_range(self)->bool:
        return True
    def outputs_non_standard_range(self)->bool:
        return not self.outputs_standard_range()
        '''
    
    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x:torch.Tensor
        # If you know how pytorch works, you can comment this checking out.
        # if not input.requires_grad:
        #     raise Exception("Set x.requires_grad to True. If you know what you are doing, you can comment this line.")
        if len(input.shape)!=2:
            raise Exception("Gates layers only accept rank-2 tensor. The shape should be[batch, gate_count * input_count]. If you have 5 data in a batch, you need 3 gates and each is AND2(which needs 2 inputs), the shape should be (5,6).")
        
        result = OR_Gate_Function.apply(input, self.alpha)
        return result
        #end of function
    pass

if 'basic test' and False:
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    layer = OR_Gate(0.1)
    print(layer.alpha.data, "alpha")
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[1.,1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    layer = OR_Gate(0.1)
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[-1.,-1,-1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    
    input = torch.tensor([[1.,1,-1,1,-1,-1]], requires_grad=True)
    layer = OR_Gate(0.1)
    pred = layer(input)
    print(pred, "pred")
    target = torch.tensor([[1.,-1,1]])
    pred.backward(target)
    print(input.grad, "input.grad")
    print()
    pass
















