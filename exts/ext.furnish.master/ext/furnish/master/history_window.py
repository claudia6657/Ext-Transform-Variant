import omni.ui as ui
import omni.usd
import omni.kit.commands
from omni.kit.usd.layers import LayerUtils
from omni.kit.viewport.utility import get_active_viewport_window
from datetime import datetime
from .style import User_Enter_Style, History_Frame_Style, Save_Window_Style, Common_Style, Icon

from .layer_controller import LayerController

#=============================
# History TreeView
#=============================
class HistoryItem(ui.AbstractItem):
    """Single item of the model"""

    def __init__(self, relative, comment, user, date, size):
        super().__init__()
        self.relative_model = ui.SimpleStringModel(relative)
        self.comment_model = ui.SimpleStringModel(comment)
        self.name_model = ui.SimpleStringModel(user)
        self.date_model = ui.SimpleStringModel(date)
        self.size_model = ui.SimpleStringModel(size)
    
    def __repr__(self):
        return f'"{self.relative_model.as_string} {self.comment_model.as_string} {self.name_model.as_string} {self.date_model.as_string} {self.size_model.as_string}"'
        
class HistoryModel(ui.AbstractItemModel):
    def __init__(self, args):
        super().__init__()
        self.on_changed(args)

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return.
            return []

        return self._children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 5

    def get_item_value_model(self, item, column_id):
        if column_id == 0:
            return item.relative_model
        elif column_id ==1:
            return item.comment_model
        elif column_id == 2:
            return item.name_model
        elif column_id == 3:
            return item.date_model
        else:
            return item.size_model
    
    def on_changed(self, args):
        regrouped = zip(*(iter(args),) * 5)
        self._children = [HistoryItem(*t) for t in regrouped]
        self._item_changed(None)

class HistoryDelegate(ui.AbstractItemDelegate):

    def build_widget(self, model, item, column_id, level, expanded):
        # TreeView Widget
        with ui.HStack(width=20):
            value_model = model.get_item_value_model(item, column_id)
            ui.Label(value_model.as_string)

    def build_header(self, column_id):
        PATHS_COLUMNS = ["file", "comment", "user", "time", "size"]
        with ui.HStack():
            ui.Spacer(width=10)
            ui.Label(PATHS_COLUMNS[column_id], name="header")

#=============================
# History WINDOW
#=============================
class HistoryUI():

    def __init__(self, controller, **kwargs):
        self.controller = controller 
        self._user_window = ui.Window('Login')
        self._history_window = ui.Window("File Control")
        self._history_window.deferred_dock_in("Property")
        self._save_window = None
        self.viewport_W = get_active_viewport_window().frame.computed_content_width
        self.viewport_H = get_active_viewport_window().frame.computed_content_height
        self.user = ''
        self.command = ''
        self.selected_checkpoint = None
        self.build_user()
        
        self._mouse_double_clicked_fn = kwargs.get("mouse_double_clicked_fn", None)

    def build_user(self) -> None:
        self._user_window.flags = ui.WINDOW_FLAGS_NO_COLLAPSE|ui.WINDOW_FLAGS_NO_RESIZE|ui.WINDOW_FLAGS_NO_TITLE_BAR|ui.WINDOW_FLAGS_NO_SCROLLBAR
        self._user_window.frame.set_style({
            "Window": {
                "background_color": 0xB1000000,
                "border_radius": 5,
            }
        })
        self._user_window.width = 320
        self._user_window.height = 150
        pos = [(self.viewport_W - self._user_window.width)/2, (self.viewport_H - self._user_window.height)/2]
        self._user_window.setPosition(pos[0], pos[1])
        
        with self._user_window.frame:
            with ui.VStack(style=User_Enter_Style):
                self.build_user_frame()
          
    def build_user_frame(self):
        self.LOGIN = ui.ScrollingFrame()
        with self.LOGIN:
            with ui.VStack(style=User_Enter_Style):
                ui.Label('ENTER USER NAME',name='title', alignment=ui.Alignment.CENTER)
                ui.Spacer(height=10)
                user = ui.Label(self.user, visible=False)
                with ui.HStack():
                    ui.Label('User Name  : ', width=ui.Percent(25), alignment=ui.Alignment.RIGHT_TOP)
                    nameField = ui.StringField(height=25, alignment=ui.Alignment.H_CENTER)
                    nameField.model.add_value_changed_fn(
                        lambda m, l=user:self.setUserName(m.get_value_as_string(), user)
                    )
                
                ui.Button('Start', alignment=ui.Alignment.CENTER, height=40, clicked_fn=self.controller.on_click_user_enter)

    def build_save_window(self) -> None:
        self._save_window = ui.Window('Save', width=350, height=200)
        
        pos = [(self.viewport_W - self._save_window.width)/2, (self.viewport_H - self._save_window.height)/2]
        self._save_window.setPosition(pos[0], pos[1])
        self._save_window.flags = ui.WINDOW_FLAGS_NO_COLLAPSE|ui.WINDOW_FLAGS_NO_TITLE_BAR|ui.WINDOW_FLAGS_NO_SCROLLBAR|ui.WINDOW_FLAGS_NO_RESIZE
        self._save_window.frame.set_style({
            "Window": {
                "background_color": 0xB1000000,
                "border_radius": 5,
                "padding":5,
            }
        })
        with self._save_window.frame:
            with ui.VStack(style=Save_Window_Style):
                ui.Label('Save New File' ,name='title' ,alignment=ui.Alignment.CENTER)
                ui.Line()
                command = ui.Label(self.command, visible=False)
                ui.Label('Comment:', alignment=ui.Alignment.LEFT_BOTTOM, name='command_Field')
                commandField = ui.StringField(height=40, alignment=ui.Alignment.H_CENTER)
                commandField.model.add_value_changed_fn(
                    lambda m, l=command:self.setCommand(m.get_value_as_string(), command)
                )
                with ui.HStack(alignment=ui.Alignment.CENTER):
                    ui.Button('  Save  ', alignment=ui.Alignment.CENTER, height=40, clicked_fn=self._on_clicked_save_btn)
                    ui.Button(' Cancel ', height=40, alignment=ui.Alignment.CENTER, clicked_fn=self._on_clicked_cancel_btn)

    def build_history(self) -> None:
        layerpath = self.controller._layer.userBase
        layer = layerpath.split('/')
        with self._history_window.frame:
            with ui.VStack(width=ui.Percent(100), height=ui.Percent(100), style=Common_Style):                
                ui.Spacer(height=5)
                with ui.HStack(height=40):
                    ui.Label(self.user, name="TITLE")
                    ui.Button(
                        style = Icon.SAVE_STYLE, width=30, height=30, name='user', tooltip='Logout', 
                        alignment=ui.Alignment.RIGHT,
                        mouse_pressed_fn=self.reLogin,
                        image_url = Icon.User
                    )
                with ui.HStack(height=40):
                    ui.Label(layer[-1], height=25, width=100, name="SUBTITLE")
                    ui.Button(
                        style = Icon.SAVE_STYLE, width=30, height=30, name='save', tooltip='Save', 
                        alignment=ui.Alignment.LEFT_CENTER,
                        mouse_pressed_fn=self.controller._layer.save_stage,
                        image_url = Icon.Save
                    )
                    ui.Spacer()
                ui.Spacer(height=5)
                self._Hist_frame = self.build_history_list()
    
    def build_history_list(self):
        self.historyStack = self.controller._layer.get_layer_details()
        self.checkpointModel = HistoryModel(self.historyStack)
        self.delegate = HistoryDelegate()
        self._Hist_frame = ui.ScrollingFrame(
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
        )
        with self._Hist_frame:
            with ui.VStack(width=ui.Percent(100)):
                treeview = ui.TreeView(
                    self.checkpointModel, 
                    root_visible=False,
                    header_visible=True,
                    delegate = self.delegate,
                    selection_changed_fn = self.on_checkpoint_selection_changed,
                    style={"TreeView.Item": {"margin_height": 7, "margin_width": 5,"font_size": 16}}
                )
                treeview.column_widths = [ui.Pixel(0), ui.Fraction(1), ui.Pixel(90), ui.Pixel(200), ui.Pixel(120)]
                treeview.set_mouse_double_clicked_fn(self._on_mouse_double_clicked)
                self.addNew = ui.ScrollingFrame(
                    style=History_Frame_Style, height=30, name='add', 
                    mouse_pressed_fn=lambda x, y, btn, flag, item=self.controller._layer.usedLayer:self._on_mouse_pressed_add_new(btn, item)
                )
                with self.addNew:
                    with ui.VStack(alignment=ui.Alignment.LEFT_CENTER):
                        ui.Label('+ Save As', name='name')
    
    #======================================================================================
    # Trigger
    #======================================================================================
    def on_checkpoint_selection_changed(self, selected_items):
        for item in selected_items:
            cp = item.relative_model.as_string
            self.selected_checkpoint = cp
            print(self.selected_checkpoint)
        
    def _on_mouse_double_clicked(self, x, y, btn, m):
        if btn == 0:
            if self.selected_checkpoint:
                layer = self.controller._layer.transfer_Layer(self.selected_checkpoint)
        
    def _on_mouse_pressed_add_new(self, btn, item):
        if btn == 0:
            self.build_save_window()
    
    def _on_mouse_pressed_back_to_head(self, x, y, btn, m):
        if btn == 0:
            stage = omni.usd.get_context().get_stage()
            layerPosition = LayerUtils.get_sublayer_position_in_parent(
                stage.GetRootLayer().identifier, stage.GetEditTarget().GetLayer().identifier
            )
            self.controller._layer.replace_layer(layerPosition, '')
            self.addNew.visible = True
            
    def _on_clicked_save_btn(self):
        # Save New
        stage = omni.usd.get_context().get_stage()        
        IDENTIFIER = self.controller._layer.save_layer(self.command)
        
        ''' update '''
        self._save_window.visible = False
        self.historyStack.insert(0, IDENTIFIER.split('/')[-1])
        self.historyStack.insert(1, self.command)
        self.historyStack.insert(2, self.user)
        self.historyStack.insert(3, str(datetime.now()))
        self.historyStack.insert(4, '')
        
        self.checkpointModel.on_changed(self.historyStack)
        self._save_window = None
    
    def _on_clicked_cancel_btn(self):
        self.command = ''
        self._save_window.visible = False
    
    def setUserName(self, text, userLabel):
        self.user = text
        userLabel.text = self.user
        
    def setCommand(self, text, commandLabel):
        self.command = text
        commandLabel.text = self.command
    
    def reLogin(self):
        self.controller._layer.rebuild()
        self.user = None
        self.command = None
        self.addNew = None
        self.historyStack = None
        self._save_window = None
        self._block_frame = None
        self._user_window = None
        self._userEnter_Frame = None 
        self._Hist_frame = None
        
        self.build_user()
    
    def shutdown(self):
        self.controller = None 
        self.user = None
        self.command = None
        self.addNew = None
        self.historyStack = None
        self._save_window = None
        self._block_frame = None
        self._user_window = None
        self._userEnter_Frame = None 
        self._Hist_frame = None
        self._history_window = None