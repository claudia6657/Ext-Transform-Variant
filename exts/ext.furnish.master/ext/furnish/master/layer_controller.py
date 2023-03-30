import asyncio
import omni.usd
from pxr import Sdf, Usd
import omni.kit.commands
from omni.kit.usd.layers import LayerUtils

BaseLayer = ['D:\Omniverse\AI_Park\AI_Project_Jan_v2\AI_arc_0317_VariantPL.usd']
nucleusBaseLayer = ['omniverse://wih-nucleus/DigitalTwin_Projects/AIArc_Project/AI_Project/AI_Project_Jan/AI_arc_0317_VariantPL.usd']

class LayerController():
    
    def __init__(self, controller):
        self.user = ''
        self.layerStack = None
        self.mutedLayerStack = None
        self.userLayerStack = []
        self.muteStack = []
        self.loadStack = []
        
        self.rootLayer = None
        self.userBase = None
        self.BaseLayer = None
        self.usedLayer = None
        self.newUser = None
        self.tempLayer = None
        self.default_layer_setting()

    def set_layer_by_user(self):
        """Login"""
        stage = omni.usd.get_context().get_stage()
        self.default_layer_setting()
        
        if self.user == 'manager':
            self.userBase = stage.GetRootLayer().identifier
            return True
        
        unmute = self.set_all_layers_unmute()
        if not unmute:
            return False
        
        getUserLayer = False
        self.muteStack = []
        
        for layer in self.userLayerStack:
            layerName = 'User_' + self.user
            if layer == stage.GetEditTarget().GetLayer().identifier:
                self.usedLayer = layer
                getUserLayer = True
            elif self.user not in layer:
                self.muteStack.append(layer)
            elif layerName in layer:
                userlayer = layerName + '.usd'
                if userlayer == layer.split('/')[-1] and not getUserLayer:
                    self.userBase = layer
                    getUserLayer = True
                else:
                    self.loadStack.append(layer)
            else:
                self.muteStack.append(layer)
        
        if getUserLayer:
            if self.muteStack != []:
                print(self.muteStack)
                self.set_layers_mute(self.muteStack)
                self.muteStack = []
        else:
            return False

        print(self.loadStack)
        if self.loadStack:
            self.get_temp_layer()
            self.set_layers_mute(self.loadStack)
        else:
            self.create_temp_layer()
        return True
    
    # ===========================
    # Layer Mute
    # ===========================
    
    def set_layers_mute(self, layers):
        """Mute Other User's Layer"""
        stage = omni.usd.get_context().get_stage()
        for layer in layers:
            if layer == self.usedLayer or layer == self.tempLayer:
                pass
            else:
                l = Sdf.Find(layer).identifier
                stage.MuteLayer(l)

    def set_layer_unmute(self, layers):
        """layer - identifier"""
        stage = omni.usd.get_context().get_stage()
        for layer in layers:
            stage.UnmuteLayer(layer)
        
    def set_all_layers_unmute(self) -> None:
        """Unmuted All Layers"""
        stage = omni.usd.get_context().get_stage()
        self.mutedLayerStack = stage.GetMutedLayers()
        if self.mutedLayerStack == []:
            return True

        print(self.mutedLayerStack)
        for layer in self.mutedLayerStack:
            l = Sdf.Find(layer).identifier
            stage.UnmuteLayer(l)
        return True

    def default_layer_setting(self):
        """Default Setting Layer Stacks"""
        import omni.kit.commands
        stage = omni.usd.get_context().get_stage()
        self.layerStack = stage.GetLayerStack()
        self.mutedLayerStack = stage.GetMutedLayers()
        self.rootLayer = stage.GetRootLayer()
        if self.usedLayer == None:
            self.usedLayer = self.rootLayer.identifier
        
        if self.user == '':
            omni.kit.commands.execute("SetEditTarget", layer_identifier=self.usedLayer)
        
        self.userLayerStack = []
        for layer in self.layerStack:
            if layer == self.rootLayer:
                pass
            elif layer.identifier in BaseLayer or layer.identifier in nucleusBaseLayer:
                self.BaseLayer = layer
            elif 'User' in layer.identifier:
                self.userLayerStack.append(layer.identifier)
        
        if self.mutedLayerStack:
            for layer in self.mutedLayerStack:
                identifier = Sdf.Find(layer).identifier
                if 'User' in identifier:
                    self.userLayerStack.append(identifier)
        print(self.userLayerStack)
        print(self.BaseLayer)

    # ===================================================================================
    # Layer File Commands
    # ===================================================================================
    
    def create_temp_layer(self):
        '''Create Temp Layer '''
        index = len(self.loadStack)
        path = 'omniverse://wih-nucleus/DigitalTwin_Projects/Test/FurnishExt/'+self.user+'/User_'+self.user+'_'+str(index)+'.usd'
        stage = omni.usd.get_context().get_stage()
        omni.kit.commands.execute(
            "CreateSublayerCommand",
            layer_identifier=stage.GetRootLayer().identifier,
            sublayer_position=0,
            new_layer_path=path,
            transfer_root_content=False,
            create_or_insert=False,
        )
        omni.kit.commands.execute("SetEditTarget", layer_identifier=path)
        self.tempLayer = path
        self.loadStack.append(path)
        
        return True
    
    def get_temp_layer(self):
        '''Get User Temp Layer (SubLayer Position 0)'''
        target = None
        for layer in self.loadStack:
            position = LayerUtils.get_sublayer_position_in_parent(
                self.userBase, layer
            )
            if position == 0:
                self.tempLayer = layer
            if position == 1:
                target = layer
        if target and self.tempLayer:
            omni.kit.commands.execute("SetEditTarget", layer_identifier=self.tempLayer)
        
    def transfer_Layer(self, path):
        '''Load Target History Layer By Double Click'''
        path = 'omniverse://wih-nucleus/DigitalTwin_Projects/Test/FurnishExt/' + self.user + '/' +path
        layer = Sdf.Find(path).identifier
        stage = omni.usd.get_context().get_stage()
        self.export_layer(path, stage.GetEditTarget().GetLayer().identifier)
        return layer

    def create_newUserLayer(self):
        """New User New Layer"""
        
        path = 'omniverse://wih-nucleus/DigitalTwin_Projects/Test/FurnishExt/' + self.user
        self.create_folder(path)    
        path = path + '/User_' + self.user + '.usd'

        stage = omni.usd.get_context().get_stage()
        Sdf.Layer.CreateNew(path)
        self.userBase = path
        omni.kit.commands.execute(
            "CreateSublayerCommand",
            layer_identifier=stage.GetRootLayer().identifier,
            sublayer_position=0,
            new_layer_path=path,
            transfer_root_content=False,
            create_or_insert=True,
        )
        self.create_sublayer()
        
    def create_sublayer(self):
        """New Layer"""
        import omni.kit.commands
        index = len(self.loadStack)
        path = 'omniverse://wih-nucleus/DigitalTwin_Projects/Test/FurnishExt/'+self.user+'/User_'+self.user+'_'+str(index)+'.usd'

        Sdf.Layer.CreateNew(path)
        omni.kit.commands.execute(
            "CreateSublayerCommand",
            layer_identifier=self.userBase,
            sublayer_position=0,
            new_layer_path=path,
            transfer_root_content=False,
            create_or_insert=True,
        )
        omni.kit.commands.execute("SetEditTarget", layer_identifier=path)
        self.loadStack.append(path)
        self.usedLayer = path
        self.tempLayer = path

    def export_layer(self, targetLayer, path):
        import omni.kit.commands
        # Copy and Paste Layer
        l = Sdf.Find(targetLayer)
        export = l.Export(path)
        
        if export and self.usedLayer != path:
            omni.kit.commands.execute(
                "CreateSublayerCommand",
                layer_identifier=self.userBase,
                sublayer_position=0,
                new_layer_path=path,
                transfer_root_content=False,
                create_or_insert=False,
            )
            omni.kit.commands.execute("SetEditTarget", layer_identifier=path)
        return True

    def save_layer(self, command):
        
        # Save Layer with checkpoints
        stage = omni.usd.get_context().get_stage()
        LAYER = self.save_as(stage.GetEditTarget().GetLayer().identifier, command)
        Sdf.Find(LAYER).comment = command
        Sdf.Find(LAYER).Save()
        
        return LAYER
    
    def save_as(self, target, command):            
        '''Save Layer As (New File)'''
        import omni.kit.commands
        import omni.client
        index = len(self.loadStack)
        path = 'omniverse://wih-nucleus/DigitalTwin_Projects/Test/FurnishExt/'+self.user+'/User_'+self.user+'_'+str(index)+'.usd'
        l = Sdf.Find(target)
        export = l.Export(path)
        stage = omni.usd.get_context().get_stage()
        dirty = omni.usd.get_dirty_layers(stage, True)
        
        def save(resault, err):
            if resault:
                omni.client.create_checkpoint(path, command)
            
        if export:
            omni.kit.commands.execute(
                "CreateSublayerCommand",
                layer_identifier=self.userBase,
                sublayer_position=1,
                new_layer_path=path,
                transfer_root_content=False,
                create_or_insert=False,
            )
            self.loadStack.append(path)
            self.set_layers_mute([path])
            
            omni.kit.window.file.save_layers(
                '', dirty, save, True, command
            )
            
        return path

    def save_stage(self, x, y, btn, m):
        '''Simplely Save Stage(Including All SubLayer in Stage) No Command'''
        stage = omni.usd.get_context().get_stage()
        stage.Save()
        print('Stage Saved !')

    #======================================================================================
    # Layer Commands
    #======================================================================================
    def get_layer_comment(self, layer):
        """Get comment by layer(user)"""
        comment = Sdf.Find(layer).comment
        
        return comment
    
    def get_layer_details(self):
        layerDetails = []
        # Get Checkpoints        
        self.BaseLayer
        for i in range(len(self.loadStack)):
            t = -1
            newestCheckpoints = self.get_layer_comment(self.loadStack[i])
            if not newestCheckpoints:
                newestCheckpoints = '. . .'
            detail = omni.client.stat(self.loadStack[i])[1]
            SIZE = str(detail.size/1000) + ' KB'
            layerDetails.append(detail.relative_path)

            layerDetails.append(newestCheckpoints)
            
            layerDetails.append(self.user)
            layerDetails.append(str(detail.modified_time))
            layerDetails.append(SIZE)
        return layerDetails
        
    #======================================================================================
    # Comment
    #======================================================================================
    def get_current_layer_checkpoints(self):
        """Get all Checkpoints by layer(user)"""
        stage = omni.usd.get_context().get_stage()
        url = stage.GetEditTarget().GetLayer().identifier
        checkpoints = omni.client.list_checkpoints(url)[1]
        
        return checkpoints

    def create_folder(self, path):
        omni.client.create_folder(path)

    def rebuild(self):
        self.user = ''
        self.layerStack = None
        self.mutedLayerStack = None
        self.userLayerStack = None
        self.muteStack = None
        self.loadStack = None
        self.rootLayer = None
        self.BaseLayer = None
        self.usedLayer = None
        self.newUser = None
        self.tempLayer = None

    def shutdown(self):
        self.user = ''
        self.layerStack = None
        self.mutedLayerStack = None
        self.userLayerStack = None
        self.muteStack = None
        self.loadStack = None
        
        self.rootLayer = None
        self.BaseLayer = None
        self.usedLayer = None
        self.newUser = None
        self.tempLayer = None