"""
Dispersion Stack Viewer - Debug tool to visualize individual dispersion images during stacking
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QWidget, QGridLayout, QPushButton)
from PyQt5.QtCore import Qt
import pyqtgraph as pqg
import numpy as np
from .pyqtgraph_utils import createImageItem


class DispersionStackViewer(QDialog):
    """Window to display all individual dispersion images used in stacking"""
    
    def __init__(self, dispersion_data_list, parent=None, update_callback=None):
        """
        Initialize the viewer
        
        Args:
            dispersion_data_list: List of dicts containing:
                - 'shot_idx': shot index
                - 'FV': dispersion image (2D array)
                - 'fs': frequency array
                - 'vs': velocity array
                - 'source_pos': source position
                - 'window_min': window minimum position
                - 'window_max': window maximum position
                - 'edge_offset': offset from window edge
                - 'shot_side': 'Left only' or 'Right only'
                - 'colormap': colormap name (optional, default 'plasma')
                - 'norm_per_freq': normalization flag (optional, default True)
                - 'saturation': saturation factor (optional, default 1.0)
            parent: Parent widget
            update_callback: Function to call when selection changes
        """
        super().__init__(parent)
        self.dispersion_data_list = dispersion_data_list
        self.update_callback = update_callback
        self.selected_indices = set(range(len(dispersion_data_list)))  # All selected by default
        self.shot_widgets = []  # Store widget references for updating borders
        
        # Set window flags to allow maximize button and full screen
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Calculate window info from first data entry for main title
        if dispersion_data_list:
            first_data = dispersion_data_list[0]
            window_min = first_data['window_min']
            window_max = first_data['window_max']
            window_center = (window_min + window_max) / 2.0
            self.setWindowTitle(f"Dispersion Stack Viewer - {len(dispersion_data_list)} shots | Window: [{window_min:.1f}, {window_max:.1f}] m (center: {window_center:.1f} m)")
        else:
            self.setWindowTitle(f"Dispersion Stack Viewer - {len(dispersion_data_list)} shots")
        
        self.resize(1400, 900)
        
        self.initUI()
        
    def initUI(self):
        """Initialize the user interface"""
        # Clear existing layout if rebuilding
        old_layout = self.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QWidget().setLayout(old_layout)  # Transfer ownership to delete
        
        layout = QVBoxLayout()
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for grid
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)
        
        # Calculate grid dimensions (try to make roughly square)
        n_shots = len(self.dispersion_data_list)
        n_cols = int(np.ceil(np.sqrt(n_shots)))
        n_rows = int(np.ceil(n_shots / n_cols))
        
        # Create dispersion plots in grid
        for idx, data in enumerate(self.dispersion_data_list):
            row = idx // n_cols
            col = idx % n_cols
            
            # Create widget for this shot
            shot_widget = self._create_shot_widget(data, idx)
            self.shot_widgets.append(shot_widget)
            grid.addWidget(shot_widget, row, col)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def _create_shot_widget(self, data, idx):
        """Create a widget showing one dispersion image with info"""
        widget = QWidget()
        widget.setMinimumSize(300, 320)
        
        # Store index for click handling
        widget.shot_index = idx
        
        # Make widget clickable
        widget.mousePressEvent = lambda event: self._toggle_selection(idx)
        
        # Set initial border (green = selected)
        widget.setStyleSheet("QWidget { border: 3px solid #00ff00; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Extract shot info
        shot_idx = data['shot_idx']
        source_pos = data['source_pos']
        edge_offset = data['edge_offset']
        shot_side = data['shot_side']
        offset_type = data.get('offset_type', 'Distance (m)')  # Default to distance if not provided
        
        # Determine offset unit
        if offset_type == 'Number of traces':
            offset_unit = 'traces'
        else:
            offset_unit = 'm'
        
        # Dispersion image plot
        plot_widget = pqg.PlotWidget()
        plot_widget.setMinimumHeight(280)
        
        # Set title with shot-specific info including unit
        title_text = f"Shot {shot_idx} | Source: {source_pos:.1f} m | {shot_side} | Offset: {edge_offset:.1f} {offset_unit}"
        plot_widget.setTitle(title_text, size='9pt')
        
        FV = data['FV']
        fs = data['fs']
        vs = data['vs']
        
        # Get visualization parameters from data (use same as main window)
        colormap = data.get('colormap', 'plasma')
        norm_per_freq = data.get('norm_per_freq', True)
        saturation = data.get('saturation', 1.0)
        
        # Apply normalization if requested
        FV_display = FV.copy()
        if norm_per_freq:
            # Normalize per frequency
            for i in range(FV_display.shape[0]):
                row = FV_display[i, :]
                max_val = np.max(np.abs(row))
                if max_val > 0:
                    FV_display[i, :] = row / max_val
        
        # Apply saturation
        if saturation != 1.0:
            FV_display = FV_display * saturation
        
        # Create image item using the same function as main dispersion plot
        # FV has shape (n_frequencies, n_velocities), pass FV.T like in main code
        image_item = createImageItem(FV_display.T, fs, vs, colormap=colormap)
        
        plot_widget.addItem(image_item)
        plot_widget.setLabel('left', 'Velocity (m/s)')
        plot_widget.setLabel('bottom', 'Frequency (Hz)')
        plot_widget.showAxis('top', False)
        plot_widget.showAxis('right', False)
        
        # Set ranges
        if len(fs) > 0 and len(vs) > 0:
            plot_widget.setXRange(fs[0], fs[-1], padding=0)
            plot_widget.setYRange(vs[0], vs[-1], padding=0)
        
        layout.addWidget(plot_widget)
        
        return widget
    
    def _toggle_selection(self, idx):
        """Toggle selection state for a shot"""
        if idx in self.selected_indices:
            # Don't allow deselecting the last selected image
            if len(self.selected_indices) <= 1:
                return
            self.selected_indices.remove(idx)
            # Set red border for unselected
            self.shot_widgets[idx].setStyleSheet("QWidget { border: 3px solid #ff0000; }")
        else:
            self.selected_indices.add(idx)
            # Set green border for selected
            self.shot_widgets[idx].setStyleSheet("QWidget { border: 3px solid #00ff00; }")
        
        # Call update callback to refresh main view
        if self.update_callback:
            self.update_callback()
    
    def update_images(self, dispersion_data_list):
        """Update all dispersion images with new data without recreating the window"""
        # If number of shots changed, we need to rebuild the entire UI
        if len(dispersion_data_list) != len(self.shot_widgets):
            self.dispersion_data_list = dispersion_data_list
            # Reset selection to all shots
            self.selected_indices = set(range(len(dispersion_data_list)))
            self.shot_widgets = []
            # Rebuild UI
            self.initUI()
            return
        
        self.dispersion_data_list = dispersion_data_list
        
        # Update window title
        if dispersion_data_list:
            first_data = dispersion_data_list[0]
            window_min = first_data['window_min']
            window_max = first_data['window_max']
            window_center = (window_min + window_max) / 2.0
            self.setWindowTitle(f"Dispersion Stack Viewer - {len(dispersion_data_list)} shots | Window: [{window_min:.1f}, {window_max:.1f}] m (center: {window_center:.1f} m)")
        
        # Update each shot widget's image
        for idx, data in enumerate(dispersion_data_list):
            
            widget = self.shot_widgets[idx]
            # Find the plot widget (should be the first child in layout)
            layout = widget.layout()
            if layout and layout.count() > 0:
                plot_widget = layout.itemAt(0).widget()
                if isinstance(plot_widget, pqg.PlotWidget):
                    # Extract data
                    FV = data['FV']
                    fs = data['fs']
                    vs = data['vs']
                    shot_idx = data['shot_idx']
                    source_pos = data['source_pos']
                    edge_offset = data['edge_offset']
                    shot_side = data['shot_side']
                    offset_type = data.get('offset_type', 'Distance (m)')
                    
                    # Determine offset unit
                    if offset_type == 'Number of traces':
                        offset_unit = 'traces'
                    else:
                        offset_unit = 'm'
                    
                    # Update title
                    title_text = f"Shot {shot_idx} | Source: {source_pos:.1f} m | {shot_side} | Offset: {edge_offset:.1f} {offset_unit}"
                    plot_widget.setTitle(title_text, size='9pt')
                    
                    # Get visualization parameters
                    colormap = data.get('colormap', 'plasma')
                    norm_per_freq = data.get('norm_per_freq', True)
                    saturation = data.get('saturation', 1.0)
                    
                    # Apply normalization
                    FV_display = FV.copy()
                    if norm_per_freq:
                        for i in range(FV_display.shape[0]):
                            row = FV_display[i, :]
                            max_val = np.max(np.abs(row))
                            if max_val > 0:
                                FV_display[i, :] = row / max_val
                    
                    # Apply saturation
                    if saturation != 1.0:
                        FV_display = FV_display * saturation
                    
                    # Clear old items
                    plot_widget.clear()
                    
                    # Create new image item
                    image_item = createImageItem(FV_display.T, fs, vs, colormap=colormap)
                    plot_widget.addItem(image_item)
                    
                    # Update ranges
                    if len(fs) > 0 and len(vs) > 0:
                        plot_widget.setXRange(fs[0], fs[-1], padding=0)
                        plot_widget.setYRange(vs[0], vs[-1], padding=0)


def show_dispersion_stack_viewer(dispersion_data_list, parent=None, update_callback=None):
    """
    Convenience function to show the dispersion stack viewer
    
    Args:
        dispersion_data_list: List of dispersion data dicts
        parent: Parent widget
        update_callback: Function to call when selection changes
        
    Returns:
        DispersionStackViewer instance
    """
    if not dispersion_data_list:
        return None
    
    viewer = DispersionStackViewer(dispersion_data_list, parent, update_callback)
    viewer.show()
    return viewer
