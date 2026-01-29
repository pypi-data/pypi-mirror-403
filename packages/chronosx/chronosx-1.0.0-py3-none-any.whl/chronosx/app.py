#!/usr/bin/env python3
"""ChronosX - Minimal macOS menubar chronometer."""

import json
import objc
from datetime import datetime
from pathlib import Path
from AppKit import (
    NSApplication, NSApp, NSStatusBar, NSVariableStatusItemLength,
    NSWindow, NSScrollView, NSTableView, NSButton, NSFont, NSColor,
    NSView, NSTableColumn, NSBackingStoreBuffered, NSFocusRingTypeNone,
    NSTableViewSelectionHighlightStyleNone, NSRoundedBezelStyle,
    NSApplicationActivationPolicyAccessory, NSPopUpMenuWindowLevel,
    NSWindowStyleMaskBorderless, NSPanel, NSWindowStyleMaskNonactivatingPanel
)
from Foundation import NSObject, NSTimer, NSMakeRect, NSMakeSize, NSRunLoop, NSDefaultRunLoopMode


# --- Storage ---

class LapStorage:
    """Persistent JSON storage for laps."""
    
    def __init__(self):
        self.path = Path.home() / ".chronosx_laps.json"
        self.laps = self._load()
    
    def _load(self) -> list:
        if self.path.exists():
            try:
                with open(self.path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save(self):
        with open(self.path, 'w') as f:
            json.dump(self.laps, f, indent=2)
    
    def add(self, seconds: float) -> dict:
        lap = {
            "id": len(self.laps),
            "duration": seconds,
            "title": f"Lap {len(self.laps) + 1}",
            "timestamp": datetime.now().isoformat()
        }
        self.laps.append(lap)
        self._save()
        return lap
    
    def update_title(self, lap_id: int, title: str):
        for lap in self.laps:
            if lap["id"] == lap_id:
                lap["title"] = title
                self._save()
                return
    
    def clear(self):
        self.laps = []
        self._save()
    
    def all_reversed(self) -> list:
        return list(reversed(self.laps))


# --- Helpers ---

def format_time(seconds: float, with_ms: bool = True) -> str:
    """Format as MM:SS.m (with tenths) or MM:SS."""
    m, s = divmod(seconds, 60)
    if with_ms:
        tenths = int((s % 1) * 10)
        return f"{int(m):02d}:{int(s):02d}.{tenths}"
    else:
        return f"{int(m):02d}:{int(s):02d}"


class TimerHelper(NSObject):
    """Helper to receive NSTimer callbacks."""
    
    @objc.python_method
    def initWithCallback_(self, callback):
        self = objc.super(TimerHelper, self).init()
        if self:
            self.callback = callback
        return self
    
    def tick_(self, timer):
        if self.callback:
            self.callback()


# --- Custom Status Item Button ---

class StatusItemButton(NSView):
    """Custom view for status bar with click detection."""
    
    @objc.python_method
    def initWithFrame_controller_(self, frame, controller):
        self = objc.super(StatusItemButton, self).initWithFrame_(frame)
        if self:
            self.controller = controller
        return self
    
    def mouseDown_(self, event):
        self.controller.toggle()
    
    def rightMouseDown_(self, event):
        self.controller.show_laps_window()
    
    def drawRect_(self, rect):
        text = self.controller.display_text
        is_icon = (text == self.controller.ICON_IDLE)
        
        if is_icon:
            font = NSFont.systemFontOfSize_(18)
            y_offset = -1  # Push down for visual centering
        else:
            font = NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0.0)
            y_offset = 0
        
        attrs = {"NSFont": font, "NSColor": NSColor.labelColor()}
        ns_string = objc.lookUpClass('NSAttributedString').alloc().initWithString_attributes_(text, attrs)
        text_size = ns_string.size()
        x = (rect.size.width - text_size.width) / 2
        y = (rect.size.height - text_size.height) / 2 + y_offset
        ns_string.drawAtPoint_((x, y))


# --- Table Data Source ---

class LapsTableDataSource(NSObject):
    """Data source for the laps table."""
    
    @objc.python_method  
    def initWithStorage_(self, storage):
        self = objc.super(LapsTableDataSource, self).init()
        if self:
            self.storage = storage
            self.laps = storage.all_reversed()
        return self
    
    @objc.python_method
    def refresh(self):
        self.laps = self.storage.all_reversed()
    
    def numberOfRowsInTableView_(self, table):
        return len(self.laps)
    
    def tableView_objectValueForTableColumn_row_(self, table, column, row):
        if row >= len(self.laps):
            return ""
        lap = self.laps[row]
        col_id = column.identifier()
        if col_id == "time":
            return format_time(lap["duration"], with_ms=False)
        elif col_id == "title":
            return lap["title"]
        return ""
    
    def tableView_setObjectValue_forTableColumn_row_(self, table, value, column, row):
        if column.identifier() == "title" and row < len(self.laps):
            lap = self.laps[row]
            self.storage.update_title(lap["id"], value)
            self.refresh()


# --- Custom Panel ---

class EditablePanel(NSPanel):
    """Panel that allows text editing and closes on outside click."""
    
    def canBecomeKeyWindow(self):
        return True
    
    def canBecomeMainWindow(self):
        return False


class PopupWindowDelegate(NSObject):
    """Delegate to close window when it loses focus."""
    
    @objc.python_method
    def initWithWindow_table_(self, window, table):
        self = objc.super(PopupWindowDelegate, self).init()
        if self:
            self.window = window
            self.table = table
        return self
    
    def windowDidResignKey_(self, notification):
        if self.window and self.table:
            if self.table.currentEditor():
                return
            self.window.close()


# --- Laps Window ---

class LapsWindow:
    """Borderless popup showing lap history."""
    
    WINDOW_WIDTH = 384
    WINDOW_HEIGHT = 200
    BUTTON_HEIGHT = 22
    
    def __init__(self, storage, get_button_position):
        self.storage = storage
        self.get_button_position = get_button_position
        self.window = None
        self.table = None
        self.data_source = None
        self.delegate = None
    
    def show(self):
        if self.window:
            self.window.close()
            self.window = None
        
        button_rect = self.get_button_position()
        x = button_rect.origin.x
        y = button_rect.origin.y - self.WINDOW_HEIGHT - 4
        
        frame = NSMakeRect(x, y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.window = EditablePanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel, 
            NSBackingStoreBuffered, False
        )
        self.window.setLevel_(NSPopUpMenuWindowLevel)
        self.window.setHasShadow_(True)
        self.window.setOpaque_(False)
        
        bg_color = NSColor.windowBackgroundColor().colorWithAlphaComponent_(0.75)
        self.window.setBackgroundColor_(bg_color)
        
        self.window.contentView().setWantsLayer_(True)
        self.window.contentView().layer().setCornerRadius_(8.0)
        self.window.contentView().layer().setMasksToBounds_(True)
        
        padding = 8
        table_height = self.WINDOW_HEIGHT - self.BUTTON_HEIGHT - padding * 3
        scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(padding, self.BUTTON_HEIGHT + padding * 2, self.WINDOW_WIDTH - padding * 2, table_height)
        )
        scroll.setHasVerticalScroller_(True)
        scroll.setBorderType_(0)
        scroll.setDrawsBackground_(False)
        
        self.table = NSTableView.alloc().initWithFrame_(scroll.bounds())
        self.table.setSelectionHighlightStyle_(NSTableViewSelectionHighlightStyleNone)
        self.table.setFocusRingType_(NSFocusRingTypeNone)
        self.table.setRowHeight_(22)
        self.table.setGridStyleMask_(0)
        self.table.setHeaderView_(None)
        self.table.setBackgroundColor_(NSColor.clearColor())
        self.table.setAllowsColumnSelection_(False)
        
        time_col = NSTableColumn.alloc().initWithIdentifier_("time")
        time_col.setWidth_(60)
        time_col.setEditable_(False)
        self.table.addTableColumn_(time_col)
        
        title_col = NSTableColumn.alloc().initWithIdentifier_("title")
        title_col.setWidth_(self.WINDOW_WIDTH - 90)
        title_col.setEditable_(True)
        self.table.addTableColumn_(title_col)
        
        self.data_source = LapsTableDataSource.alloc().initWithStorage_(self.storage)
        self.table.setDataSource_(self.data_source)
        self.table.setDelegate_(self.data_source)
        
        scroll.setDocumentView_(self.table)
        self.window.contentView().addSubview_(scroll)
        
        btn_font = NSFont.systemFontOfSize_(11)
        
        clear_btn = NSButton.alloc().initWithFrame_(NSMakeRect(padding, padding, 54, self.BUTTON_HEIGHT))
        clear_btn.setTitle_("Clear")
        clear_btn.setBezelStyle_(NSRoundedBezelStyle)
        clear_btn.setFont_(btn_font)
        clear_btn.setTarget_(self)
        clear_btn.setAction_(objc.selector(self.clear_, signature=b'v@:@'))
        self.window.contentView().addSubview_(clear_btn)
        
        exit_btn = NSButton.alloc().initWithFrame_(NSMakeRect(self.WINDOW_WIDTH - padding - 46, padding, 46, self.BUTTON_HEIGHT))
        exit_btn.setTitle_("Exit")
        exit_btn.setBezelStyle_(NSRoundedBezelStyle)
        exit_btn.setFont_(btn_font)
        exit_btn.setTarget_(self)
        exit_btn.setAction_(objc.selector(self.exit_, signature=b'v@:@'))
        self.window.contentView().addSubview_(exit_btn)
        
        self.delegate = PopupWindowDelegate.alloc().initWithWindow_table_(self.window, self.table)
        self.window.setDelegate_(self.delegate)
        
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
    
    def clear_(self, sender):
        self.storage.clear()
        self.data_source.refresh()
        self.table.reloadData()
    
    def exit_(self, sender):
        NSApp.terminate_(None)


# --- Main Controller ---

class ChronometerController(NSObject):
    """Main app controller."""
    
    ICON_IDLE = "◉"
    TICK_INTERVAL = 0.1
    
    @objc.python_method
    def init(self):
        self = objc.super(ChronometerController, self).init()
        if self:
            self.storage = LapStorage()
            self.laps_window = LapsWindow(self.storage, self.get_button_screen_position)
            
            self.running = False
            self.start_time = None
            self.elapsed = 0.0
            self.display_text = self.ICON_IDLE
            
            self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            self.button = StatusItemButton.alloc().initWithFrame_controller_(NSMakeRect(0, 0, 30, 22), self)
            self.status_item.setView_(self.button)
            self._resize_button()
            
            self.timer_helper = TimerHelper.alloc().initWithCallback_(self._tick)
            self.timer = None
        return self
    
    @objc.python_method
    def get_button_screen_position(self):
        button_frame = self.button.frame()
        window = self.button.window()
        if window:
            return window.convertRectToScreen_(button_frame)
        return NSMakeRect(800, 800, 50, 22)
    
    @objc.python_method
    def toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()
    
    @objc.python_method
    def _start(self):
        self.running = True
        self.start_time = datetime.now()
        self.elapsed = 0.0
        self._update_display()
        self.timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            self.TICK_INTERVAL, self.timer_helper, "tick:", None, True
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
    
    @objc.python_method
    def _stop(self):
        self.running = False
        if self.timer:
            self.timer.invalidate()
            self.timer = None
        if self.start_time:
            self.elapsed = (datetime.now() - self.start_time).total_seconds()
            if self.elapsed >= 0.5:
                self.storage.add(self.elapsed)
        self.display_text = self.ICON_IDLE
        self.start_time = None
        self.button.setNeedsDisplay_(True)
        self._resize_button()
    
    @objc.python_method
    def _tick(self):
        if self.running and self.start_time:
            self.elapsed = (datetime.now() - self.start_time).total_seconds()
            self._update_display()
    
    @objc.python_method
    def _update_display(self):
        self.display_text = format_time(self.elapsed, with_ms=True)
        self.button.setNeedsDisplay_(True)
        self._resize_button()
    
    @objc.python_method
    def _resize_button(self):
        font = NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0.0)
        attrs = {"NSFont": font}
        ns_str = objc.lookUpClass('NSAttributedString').alloc().initWithString_attributes_(self.display_text, attrs)
        width = max(30, ns_str.size().width + 16)
        self.button.setFrameSize_(NSMakeSize(width, 22))
        self.status_item.setLength_(width)
    
    @objc.python_method
    def show_laps_window(self):
        self.laps_window.show()


_controller = None


def main():
    """Entry point for the application."""
    global _controller
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    _controller = ChronometerController.alloc().init()
    app.run()


if __name__ == "__main__":
    main()
