#!/usr/bin/env python3
"""
NMR Spectra Simulator Web Application

Flask-based web interface for the NMR spectra simulation application.
"""

from flask import Flask, request, jsonify, render_template, send_file
import io
import json
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import tempfile
import logging
from logging.handlers import RotatingFileHandler

# Local project imports (may raise if modules missing)
try:
    from nmr_simulator import Spectrum, Peak, NMRSimulator
    from visual_multiplet_grouper import VisualMultipletGrouper
    from nmr_data_input import NMRDataParser
except Exception:
    Spectrum = None
    Peak = None
    NMRSimulator = None
    VisualMultipletGrouper = None
    NMRDataParser = None

app = Flask(__name__)

# Configure logging: console + rotating file
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)

try:
    log_path = os.path.join(os.path.dirname(__file__), 'web_app.log')
except Exception:
    log_path = os.path.join(tempfile.gettempdir(), 'web_app.log')
file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

app.logger.setLevel(logging.DEBUG)
app.logger.debug(f'Logging initialized. File: {log_path}')

class NMRWebApp:
    def __init__(self):
        self.last_spectrum_data = None
        # Attempt to load persisted last_spectrum_data from disk
        try:
            storage_path = os.path.join(tempfile.gettempdir(), 'nmr_last_spectrum.json')
            print(f"Checking for persisted last_spectrum_data at: {storage_path}")
            if os.path.exists(storage_path):
                with open(storage_path, 'r', encoding='utf-8') as sf:
                    self.last_spectrum_data = json.load(sf)
                    print(f"Loaded persisted last_spectrum_data from {storage_path}")
        except Exception as e:
            print(f"Failed to load persisted last_spectrum_data: {e}")
        # Instantiate visual grouper if available
        try:
            if VisualMultipletGrouper is not None:
                # prefer numeric mode for 1H where applicable
                self.visual_grouper = VisualMultipletGrouper(use_numbers_for_1H=True)
            else:
                self.visual_grouper = None
        except Exception as e:
            print(f"Failed to instantiate VisualMultipletGrouper: {e}")
            self.visual_grouper = None
        # store last generated spectrum object for export
        self.last_spectrum = None

    def generate_spectrum_plot_from_data(self, data):
        """Compatibility wrapper: build peaks list from stored spectrum dict and call generate_spectrum_plot."""
        try:
            peaks = []
            for p in data.get('peaks', []):
                # Accept either 'chemical_shift' or 'shift' keys and coerce to float when possible
                raw_shift = p.get('chemical_shift') if isinstance(p, dict) else None
                if raw_shift is None and isinstance(p, dict):
                    raw_shift = p.get('shift')
                try:
                    shift_val = float(raw_shift) if raw_shift is not None else None
                except Exception:
                    shift_val = None

                multiplicity = p.get('multiplicity', 's') if isinstance(p, dict) else 's'
                integration = p.get('integration', 1.0) if isinstance(p, dict) else 1.0
                coupling = p.get('coupling_constants', []) if isinstance(p, dict) else []
                # Preserve per-peak width/linewidth and intensity so edits survive round-trips
                width = None
                if isinstance(p, dict):
                    width = p.get('width') if 'width' in p else p.get('linewidth') if 'linewidth' in p else None
                intensity = p.get('intensity') if isinstance(p, dict) else None

                # Skip peaks without a numeric shift to avoid None-type errors
                if shift_val is None:
                    continue

                peak_entry = {
                    'shift': shift_val,
                    'multiplicity': multiplicity,
                    'integration': integration,
                    'coupling': coupling or [],
                    'raw_data': str(p)
                }
                if width is not None:
                    peak_entry['width'] = width
                if intensity is not None:
                    peak_entry['intensity'] = intensity
                peaks.append(peak_entry)

            # Retrieve generation parameters from stored data (or use defaults)
            resolution = data.get('resolution', 8192)
            noise_level = data.get('noise_level', 0.0)
            default_linewidth = data.get('default_linewidth', 2.0)
            enable_multiplet_grouping = data.get('enable_multiplet_grouping', True)
            grouping_tolerance = data.get('grouping_tolerance', 0.3)
            
            print(f"generate_spectrum_plot_from_data: using resolution={resolution}, noise_level={noise_level}, linewidth={default_linewidth}")
            
            return self.generate_spectrum_plot(
                peaks,
                nucleus=data.get('nucleus', '1H'),
                field_strength=data.get('field_strength', 400),
                spectral_width=12.0,
                resolution=resolution,
                noise_level=noise_level,
                default_linewidth=default_linewidth,
                enable_multiplet_grouping=enable_multiplet_grouping,
                grouping_tolerance=grouping_tolerance
            )
        except Exception as e:
            print(f"Error in generate_spectrum_plot_from_data: {e}")
            import traceback
            traceback.print_exc()
            return None, 0

    def parse_nmr_data(self, data_text, nucleus="1H"):
        """Parse NMR data from text input with project parser or a simple fallback.

        Returns a list of dicts with keys: 'shift', 'multiplicity', 'coupling', 'integration', 'raw_data'.
        """
        if not data_text:
            return []

        # Try project parser if available
        try:
            if NMRDataParser is not None:
                parser = NMRDataParser()
                if hasattr(parser, 'parse_nmr_text'):
                    peaks = parser.parse_nmr_text(data_text, nucleus)
                elif hasattr(parser, 'parse'):
                    peaks = parser.parse(data_text, nucleus)
                else:
                    peaks = []

                web_peaks = []
                for peak in peaks:
                    if isinstance(peak, dict):
                        shift = peak.get('shift') or peak.get('chemical_shift') or 0.0
                        multiplicity = peak.get('multiplicity', 's')
                        coupling = peak.get('coupling', peak.get('coupling_constants', [])) or []
                        if not isinstance(coupling, list):
                            try:
                                coupling = [float(coupling)]
                            except Exception:
                                coupling = []
                        integration = peak.get('integration', peak.get('area', 1.0))
                        try:
                            shift = float(shift)
                        except Exception:
                            shift = 0.0
                        try:
                            integration = float(integration)
                        except Exception:
                            integration = 1.0
                        web_peaks.append({
                            'shift': shift,
                            'multiplicity': multiplicity,
                            'coupling': coupling,
                            'integration': integration,
                            'raw_data': str(peak)
                        })
                if web_peaks:
                    return web_peaks
        except Exception as e:
            print(f"Project parser failed: {e}")

        # Fallback: very simple line-based parser (extract first float as chemical shift)
        web_peaks = []
        for line in data_text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            tokens = line.replace(',', ' ').split()
            shift = None
            for tok in tokens:
                try:
                    # Accept comma or locale-insensitive floats
                    val = float(tok)
                    shift = val
                    break
                except Exception:
                    # maybe token like '7.26(s)'
                    cleaned = ''.join(ch for ch in tok if (ch.isdigit() or ch in '.-'))
                    try:
                        val = float(cleaned) if cleaned else None
                        if val is not None:
                            shift = val
                            break
                    except Exception:
                        continue

            if shift is None:
                continue
            multiplicity = 's'
            integration = 1.0
            coupling = []
            web_peaks.append({'shift': float(shift), 'multiplicity': multiplicity, 'coupling': coupling, 'integration': integration, 'raw_data': line})

        return web_peaks

    def _apply_visual_groups(self, spectrum, annotated_peaks, groups):
        """Apply visual grouping metadata to Spectrum peaks (best-effort)."""
        try:
            # annotated_peaks: iterable of dict-like items with shift info
            # groups: iterable of group objects or dicts with membership info
            for gid, group in enumerate(groups):
                # determine peaks in this group
                members = []
                try:
                    members = getattr(group, 'peaks', None) or getattr(group, 'members', None) or []
                except Exception:
                    members = []
                
                # Get group assignment label (e.g., "A", "B", "C")
                group_assignment = getattr(group, 'assignment', str(gid + 1))
                group_integration = sum(getattr(m, 'integration', 1.0) for m in members) if members and hasattr(members[0], 'integration') else len(members) if members else 1

                print(f"_apply_visual_groups: group {gid} (assignment={group_assignment}), {len(members)} members")
                
                for mp in members:
                    # mp might be a dict with 'shift' or a simple float
                    try:
                        shift = None
                        if isinstance(mp, dict):
                            shift = mp.get('shift') or mp.get('chemical_shift')
                        else:
                            # maybe an object with chemical_shift
                            shift = getattr(mp, 'chemical_shift', None)
                        if shift is None and isinstance(mp, (int, float)):
                            shift = float(mp)
                        
                        if shift is None:
                            continue
                        
                        # find closest peak in spectrum
                        closest = None
                        best_diff = 1e6
                        for p in spectrum.peaks:
                            diff = abs(p.chemical_shift - float(shift))
                            if diff < best_diff:
                                best_diff = diff
                                closest = p
                        
                        if closest and best_diff < 0.05:
                            setattr(closest, 'visual_group_id', gid)
                            setattr(closest, 'visual_assignment', group_assignment)
                            setattr(closest, 'is_visual_center', getattr(mp, 'is_center', False))
                            setattr(closest, 'group_size', len(members) if members is not None else 1)
                            setattr(closest, 'group_integration', group_integration)
                            print(f"  Assigned peak at {closest.chemical_shift:.3f} ppm to group {group_assignment}")
                    except Exception as e:
                        print(f"  Failed to assign peak: {e}")
                        continue
        except Exception as e:
            print(f"_apply_visual_groups failed: {e}")

    def generate_spectrum_plot(self, peaks, nucleus="1H", field_strength=400, 
                             spectral_width=12.0, resolution=8192, noise_level=0.0,
                             default_linewidth=2.0, enable_multiplet_grouping=True, 
                             grouping_tolerance=0.3):
        """Generate interactive spectrum plot with per-peak linewidth control."""
        print(f"generate_spectrum_plot called with {len(peaks)} peaks")
        print(f"First peak type: {type(peaks[0]) if peaks else 'No peaks'}")
        if peaks:
            print(f"First peak keys: {peaks[0].keys() if isinstance(peaks[0], dict) else 'Not dict'}")

        # Create spectrum directly and add peaks
        spectrum = Spectrum(nucleus=nucleus, field_strength=field_strength)
        spectrum.title = "User Input Spectrum"

        grouped_peaks = []  # Initialize grouped_peaks list

        # Add peaks first to determine ppm range
        for i, peak_data in enumerate(peaks):
            # Convert coupling to list if it isn't already
            coupling = peak_data.get('coupling', [])
            if isinstance(coupling, list):
                coupling_constants = coupling
            else:
                coupling_constants = [float(coupling)] if coupling is not None else []

            # Determine linewidth from peak data or keywords
            linewidth = default_linewidth
            # allow per-peak linewidth/width (ppm or Hz) to override
            # accept keys: 'width' (ppm), 'linewidth' (Hz)
            per_peak_width_ppm = None
            if 'width' in peak_data and peak_data.get('width') is not None:
                try:
                    per_peak_width_ppm = float(peak_data.get('width'))
                except Exception:
                    per_peak_width_ppm = None
            elif 'linewidth' in peak_data and peak_data.get('linewidth') is not None:
                try:
                    # linewidth provided in Hz -> convert to ppm
                    per_peak_width_ppm = float(peak_data.get('linewidth')) / float(field_strength)
                except Exception:
                    per_peak_width_ppm = None
            multiplicity = peak_data.get('multiplicity', 's').lower()

            # Check for linewidth in peak data (4th column in SDBS extended format)
            if len(str(peak_data.get('raw_data', '')).split()) >= 4:
                try:
                    linewidth = float(str(peak_data['raw_data']).split()[3])
                    print(f"Using specific linewidth {linewidth} Hz for peak at {peak_data['shift']} ppm")
                except (ValueError, IndexError):
                    pass

            # Check for broadening keywords
            elif 'br' in multiplicity:
                linewidth = 15.0  # Broad peaks
                print(f"Broad peak detected at {peak_data['shift']} ppm, using {linewidth} Hz")
            elif any(keyword in str(peak_data.get('raw_data', '')).lower() 
                    for keyword in ['nh', 'oh', 'broad']):
                linewidth = 25.0  # Very broad exchangeable protons
                print(f"NH/OH peak detected at {peak_data['shift']} ppm, using {linewidth} Hz")

            # finalize width: prefer per-peak width if available
            if per_peak_width_ppm is not None:
                width_ppm = per_peak_width_ppm
            else:
                width_ppm = (linewidth / field_strength)

            # intensity: prefer explicit 'intensity' then 'integration'
            try:
                intensity_val = float(peak_data.get('intensity', peak_data.get('integration', 1.0)))
            except Exception:
                intensity_val = 1.0

            peak = Peak(
                chemical_shift=peak_data['shift'],
                intensity=intensity_val,
                width=width_ppm,
                multiplicity=peak_data.get('multiplicity', 's'),
                coupling_constants=coupling_constants,
                integration=peak_data.get('integration', 1.0)
            )
            spectrum.add_peak(peak)
            grouped_peaks.append(peak_data)

        # Update ppm range based on peaks, but ensure minimum range
        if spectrum.peaks:
            peak_shifts = [p.chemical_shift for p in spectrum.peaks]
            min_shift = min(peak_shifts)
            max_shift = max(peak_shifts)
            margin = 1.0  # 1 ppm margin on each side

            # Ensure minimum range for better visualization
            if nucleus == '1H':
                min_range = 12.0  # Minimum 12 ppm range for 1H
            elif nucleus == '13C':
                min_range = 200.0  # Minimum 200 ppm range for 13C
            else:
                min_range = 10.0  # Default minimum range

            range_width = max_shift - min_shift + 2 * margin
            if range_width < min_range:
                center = (min_shift + max_shift) / 2
                half_range = min_range / 2
                min_shift = center - half_range
                max_shift = center + half_range

            spectrum.ppm_range = (min_shift, max_shift + 2 * margin)
            print(f"Updated ppm range to {spectrum.ppm_range} based on peaks")

        # Track multiplet groups
        multiplet_groups = 0
        if enable_multiplet_grouping and len(grouped_peaks) > 1:
            try:
                # Use visual grouper to identify multiplets
                annotated_peaks, groups = self.visual_grouper.create_visual_groups(
                    grouped_peaks, nucleus=nucleus, tolerance_ppm=grouping_tolerance
                )
                multiplet_groups = len([g for g in groups if g.peak_count > 1])
                print(f"Created {multiplet_groups} visual multiplet groups")

                # Apply visual groups to the spectrum (add metadata to existing peaks)
                self._apply_visual_groups(spectrum, annotated_peaks, groups)
            except Exception as e:
                print(f"Multiplet grouping failed: {e}")
                multiplet_groups = 0

        # Generate spectrum data
        print(f"Generating spectrum data with resolution {min(resolution, 16384)}")
        spectrum.generate_spectrum_data(resolution=min(resolution, 16384), noise_level=noise_level/100.0)
        print(f"Spectrum data generated: ppm_axis shape {spectrum.ppm_axis.shape if spectrum.ppm_axis is not None else 'None'}, data_points shape {spectrum.data_points.shape if spectrum.data_points is not None else 'None'}")
        
        # Debug: print actual ppm axis range
        if spectrum.ppm_axis is not None and len(spectrum.ppm_axis) > 0:
            print(f"Generated ppm_axis range: {spectrum.ppm_axis[0]:.2f} to {spectrum.ppm_axis[-1]:.2f}")
            print(f"ppm_range attribute: {getattr(spectrum, 'ppm_range', 'not set')}")
        
        # Store the spectrum data for export functionality (include generation parameters for edits)
        # **Store ppm_axis in ascending order (low→high) for JCAMP/Bruker compatibility**
        ppm_axis_for_export = spectrum.ppm_axis.copy()
        data_points_for_export = spectrum.data_points.copy()
        
        try:
            with open('C:\\tmp\\debug_reversal.txt', 'a') as df:
                df.write(f"BEFORE: {ppm_axis_for_export[0]:.2f} to {ppm_axis_for_export[-1]:.2f}\n")
                df.flush()
        except:
            pass
        
        logger.debug(f"After copy: ppm_axis length={len(ppm_axis_for_export) if ppm_axis_for_export is not None else None}")
        logger.debug(f"Before reversal: ppm_axis first={ppm_axis_for_export[0]:.2f}, last={ppm_axis_for_export[-1]:.2f}")
        
        if ppm_axis_for_export is not None and len(ppm_axis_for_export) > 1:
            logger.debug(f"Condition passed: checking if {ppm_axis_for_export[0]:.2f} > {ppm_axis_for_export[-1]:.2f}")
            if ppm_axis_for_export[0] > ppm_axis_for_export[-1]:
                logger.debug("YES - reversing")
                # Currently descending (high→low), reverse to ascending (low→high)
                ppm_axis_for_export = ppm_axis_for_export[::-1]
                data_points_for_export = data_points_for_export[::-1]
                # Also reverse the spectrum object's ppm_axis so exports use reversed data
                spectrum.ppm_axis = ppm_axis_for_export
                spectrum.data_points = data_points_for_export
                logger.debug(f"Reversed ppm_axis: now first={ppm_axis_for_export[0]:.2f}, last={ppm_axis_for_export[-1]:.2f}")
                print(f"✓ REVERSED spectrum.ppm_axis to ascending (low→high)")
                try:
                    with open('C:\\tmp\\debug_reversal.txt', 'a') as df:
                        df.write(f"AFTER: {ppm_axis_for_export[0]:.2f} to {ppm_axis_for_export[-1]:.2f}\n")
                        df.flush()
                except:
                    pass
            else:
                logger.debug(f"NO - already ascending, no reversal needed")
        else:
            logger.debug(f"Condition NOT passed: ppm_axis is None or length <= 1")

        
        spectrum_data = {
            'nucleus': spectrum.nucleus,
            'field_strength': spectrum.field_strength,
            'resolution': resolution,
            'noise_level': noise_level,
            'default_linewidth': default_linewidth,
            'enable_multiplet_grouping': enable_multiplet_grouping,
            'grouping_tolerance': grouping_tolerance,
            'ppm_axis': ppm_axis_for_export.tolist() if ppm_axis_for_export is not None else None,
            'data_points': data_points_for_export.tolist() if data_points_for_export is not None else None,
            'peaks': [{
                'chemical_shift': p.chemical_shift,
                'intensity': p.intensity,
                'width': p.width,
                'multiplicity': p.multiplicity,
                'integration': p.integration,
                'coupling_constants': list(p.coupling_constants) if p.coupling_constants else [],
                'visual_group_id': getattr(p, 'visual_group_id', -1),
                'visual_assignment': getattr(p, 'visual_assignment', ''),
                'is_visual_center': getattr(p, 'is_visual_center', False),
                'group_size': getattr(p, 'group_size', 1),
                'group_integration': getattr(p, 'group_integration', getattr(p, 'integration', 1.0))
            } for p in spectrum.peaks]
        }
        self.last_spectrum_data = spectrum_data
        # Persist last_spectrum_data to disk so edits survive restarts
        try:
            storage_path = os.path.join(tempfile.gettempdir(), 'nmr_last_spectrum.json')
            print(f"Persisting last_spectrum_data to: {storage_path}")
            with open(storage_path, 'w', encoding='utf-8') as sf:
                json.dump(self.last_spectrum_data, sf, ensure_ascii=False)
            print(f"Persisted last_spectrum_data to: {storage_path}")
        except Exception as e:
            print(f"Failed to persist last_spectrum_data: {e}")
        # Store the actual Spectrum object for exporters that expect it
        try:
            self.last_spectrum = spectrum
        except Exception:
            # best-effort: if storing the object fails, continue with last_spectrum_data
            pass
        print(f"Spectrum data stored for export: {spectrum.nucleus}, {len(spectrum.peaks)} peaks")

        # Get spectrum data
        x_data = spectrum.ppm_axis
        y_data = spectrum.data_points

        if x_data is None or y_data is None:
            print(f"Error: spectrum data is None - x_data: {x_data}, y_data: {y_data}")
            return None, 0

        # Check for NaN or inf values
        if np.any(np.isnan(x_data)) or np.any(np.isnan(y_data)) or np.any(np.isinf(x_data)) or np.any(np.isinf(y_data)):
            print(f"Error: spectrum data contains NaN or inf values")
            print(f"x_data range: {np.min(x_data)} to {np.max(x_data)}")
            print(f"y_data range: {np.min(y_data)} to {np.max(y_data)}")
            return None, 0

        print(f"Spectrum data ranges: x={np.min(x_data):.2f} to {np.max(x_data):.2f}, y={np.min(y_data):.2f} to {np.max(y_data):.2f}")

        # Build plot data dictionary with integral annotations below ppm scale
        plot_data_dict = {
            'data': [{
                'x': x_data.tolist(),
                'y': y_data.tolist(),
                'type': 'scatter',
                'mode': 'lines',
                'line': {'color': 'blue', 'width': 1},
                'name': f'{nucleus} NMR',
                'hovertemplate': 'δ %{x:.2f} ppm<br>Intensity %{y:.3f}<extra></extra>'
            }],
            'layout': {
                'title': f'{nucleus} NMR Spectrum ({field_strength} MHz)',
                'xaxis': {
                    'title': 'Chemical Shift (ppm)',
                    'autorange': 'reversed',
                    'showgrid': True
                },
                'yaxis': {
                    'title': 'Intensity',
                    'showgrid': True
                },
                'plot_bgcolor': 'white',
                'paper_bgcolor': 'white',
                'showlegend': False,
                'annotations': []
            }
        }
        # Add integral annotations below ppm scale for visual multiplet groups
        try:
            if hasattr(spectrum, 'peaks') and spectrum.peaks:
                # Collect unique groups by visual_assignment and show their integrations
                seen_groups = {}
                for p in spectrum.peaks:
                    va = getattr(p, 'visual_assignment', '')
                    if va and va not in seen_groups:
                        # Use group_integration if available, else per-peak integration
                        integration_val = getattr(p, 'group_integration', getattr(p, 'integration', 1.0))
                        seen_groups[va] = {
                            'shift': p.chemical_shift,
                            'integration': integration_val
                        }
                # Add annotations at bottom of plot for each unique group
                print(f"Adding {len(seen_groups)} integral annotations to plot: {list(seen_groups.keys())}")
                y_min = np.min(y_data)
                for label, info in sorted(seen_groups.items()):
                    plot_data_dict['layout']['annotations'].append({'x': info['shift'], 'y': y_min * 0.3, 'text': f"{info['integration']:.1f}", 'showarrow': False, 'font': {'size': 10, 'color': 'green'}})
        except Exception as e:
            print(f"Failed to add integral annotations: {e}")
            pass

        # Try Plotly for server-side generation; if missing, still return plot_data for frontend
        try:
            import plotly.graph_objects as go
            fig = go.Figure(plot_data_dict['data'])
            fig.update_layout(**plot_data_dict['layout'])
            plotly_data = fig.to_dict()
            return {
                'plot_data': {'data': plotly_data['data'], 'layout': plotly_data['layout']},
                'static_url': None,
                'plot_type': 'interactive',
                'plot_config': {'scrollZoom': True, 'staticPlot': False, 'doubleClick': 'reset', 'displayModeBar': True}
            }, multiplet_groups
        except ModuleNotFoundError:
            # Plotly not installed; return plot_data_dict for frontend Plotly CDN to render, plus a static PNG fallback
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(x_data, y_data, 'b-', linewidth=1.5)
                if hasattr(spectrum, 'ppm_range') and spectrum.ppm_range is not None:
                    ax.set_xlim(spectrum.ppm_range[1], spectrum.ppm_range[0])
                else:
                    ax.invert_xaxis()
                ax.set_xlabel('Chemical Shift (ppm)')
                ax.set_ylabel('Intensity')
                ax.set_title(f'{nucleus} NMR Spectrum ({field_strength} MHz)')
                ax.grid(True, alpha=0.3)
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                img_b64 = base64.b64encode(buffer.getvalue()).decode()
                plt.close(fig)
                return {'plot_data': plot_data_dict, 'static_url': img_b64, 'plot_type': 'interactive'}, multiplet_groups
            except Exception as mplt_e:
                print(f"Matplotlib fallback failed: {mplt_e}")
                return {'plot_data': plot_data_dict, 'static_url': None, 'plot_type': 'interactive'}, multiplet_groups
        except Exception as plotly_error:
            print(f"Plotly plotting failed: {plotly_error}")
            # As a fallback, return the JSON plot data without server-side rendering
            return {'plot_data': plot_data_dict, 'static_url': None, 'plot_type': 'interactive'}, multiplet_groups

# Initialize web app
nmr_app = NMRWebApp()


@app.before_request
def log_request_info():
    try:
        # Small preview of body for diagnostics
        raw = request.get_data(as_text=False) or b''
        preview = raw[:200]
        app.logger.debug(f"Incoming request: {request.method} {request.path} Headers: {dict(request.headers)} Body preview: {preview!r}")
    except Exception:
        app.logger.exception('Failed to log request info')


@app.after_request
def log_response_info(response):
    try:
        body = None
        try:
            body = response.get_data(as_text=True)
        except Exception:
            body = None
        preview = body[:1000] if body else None
        app.logger.debug(f"Response {request.method} {request.path} -> {response.status} Body preview: {preview!r}")
    except Exception:
        app.logger.exception('Failed to log response info')
    return response

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/debug_info', methods=['GET'])
def debug_info():
    """Return basic runtime debug info to confirm loaded code and supported formats."""
    try:
        fmt = ['csv', 'txt', 'png', 'peaks', 'jcamp', 'jdx', 'bruker']
        try:
            mtime = os.path.getmtime(__file__)
        except Exception:
            mtime = None
        return jsonify({'supported_formats': fmt, 'web_app_mtime': mtime}), 200
    except Exception as e:
        app.logger.exception('debug_info failed')
        return jsonify({'error': str(e)}), 500

@app.route('/simulate', methods=['POST'])
def simulate():
    """Handle spectrum simulation request."""
    try:
        data = request.json
        nmr_data = data.get('nmr_data', '')
        nucleus = data.get('nucleus', '1H')
        field_strength = int(data.get('field_strength', 400))
        noise_level = float(data.get('noise_level', 0))
        resolution = int(data.get('resolution', 8192))
        
        # New parameters for enhanced functionality
        default_linewidth = float(data.get('default_linewidth', 2.0))
        enable_multiplet_grouping = data.get('enable_multiplet_grouping', True)
        grouping_tolerance = float(data.get('grouping_tolerance', 0.3))
        
        print(f"Received simulation request:")  # Debug output
        print(f"  Nucleus: {nucleus}")
        print(f"  Field strength: {field_strength}")
        print(f"  Default linewidth: {default_linewidth} Hz")
        print(f"  Multiplet grouping: {enable_multiplet_grouping}")
        print(f"  Data length: {len(nmr_data)} chars")
        print(f"  First 200 chars: {nmr_data[:200]}")
        
        # Parse NMR data
        peaks = nmr_app.parse_nmr_data(nmr_data, nucleus)
        
        if not peaks:
            error_msg = 'No valid peaks found in input data. Please check format: either "Hz ppm Int" (SDBS) or "shift (multiplicity, integration)" format'
            print(f"Error: {error_msg}")
            return jsonify({'error': error_msg})
        
        print(f"Successfully parsed {len(peaks)} peaks")
        
        # Generate spectrum plot with enhanced parameters
        plot_result, multiplet_info = nmr_app.generate_spectrum_plot(
            peaks, nucleus, field_strength, 12.0, resolution, noise_level,
            default_linewidth, enable_multiplet_grouping, 
            grouping_tolerance
        )
        
        if plot_result is None:
            error_msg = 'Failed to generate spectrum plot'
            print(f"Error: {error_msg}")
            return jsonify({'error': error_msg})
        
        print(f"Successfully generated spectrum plot with {multiplet_info} multiplet groups")
        
        return jsonify({
            'plot_data': plot_result['plot_data'],
            'static_url': plot_result.get('static_url'),
            'peaks_count': len(peaks),
            'nucleus': nucleus,
            'field_strength': field_strength,
            'multiplet_groups': multiplet_info,
            'linewidth_info': {
                'default': default_linewidth,
                'per_peak_enabled': True
            }
        })
        
    except Exception as e:
        error_msg = f'Simulation failed: {str(e)}'
        print(f"Exception in simulate: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg})

def _ensure_ascending_ppm(x_arr, y_arr):
    """Ensure ppm_axis is in ascending order (low→high) and sort both arrays accordingly."""
    if x_arr is None or len(x_arr) == 0:
        return x_arr, y_arr
    if x_arr[0] > x_arr[-1]:  # Currently descending
        return x_arr[::-1], y_arr[::-1]  # Reverse to ascending
    return x_arr, y_arr  # Already ascending


@app.route('/export/<format>')
def export_spectrum(format):
    """Export spectrum in various formats."""
    try:
        spectrum = nmr_app.last_spectrum
        # If we don't have a Spectrum object, try the stored spectrum data
        if spectrum is None:
            data = getattr(nmr_app, 'last_spectrum_data', None)
            if data is None:
                return jsonify({'error': 'No spectrum available for export. Please run a simulation first.'})
            # Create a minimal proxy object with needed attributes
            class _SpecProxy:
                pass
            spectrum = _SpecProxy()
            spectrum.nucleus = data.get('nucleus')
            spectrum.field_strength = data.get('field_strength')
            ppm_axis = data.get('ppm_axis')
            data_points = data.get('data_points')
            # convert lists to numpy arrays where appropriate
            try:
                import numpy as _np
                spectrum.ppm_axis = _np.array(ppm_axis) if ppm_axis is not None else None
                spectrum.data_points = _np.array(data_points) if data_points is not None else None
            except Exception:
                spectrum.ppm_axis = ppm_axis
                spectrum.data_points = data_points
            # Try to set a sensible ppm_range for proxy spectra (used by PNG export)
            try:
                import numpy as _np
                if spectrum.ppm_axis is not None:
                    _min = float(_np.min(spectrum.ppm_axis))
                    _max = float(_np.max(spectrum.ppm_axis))
                    spectrum.ppm_range = (_min, _max)
                else:
                    spectrum.ppm_range = (0.0, 10.0)
            except Exception:
                try:
                    spectrum.ppm_range = (0.0, 10.0)
                except Exception:
                    pass
            # construct simple peaks list
            peaks_list = []
            for p in data.get('peaks', []):
                class _P: pass
                pp = _P()
                pp.chemical_shift = p.get('chemical_shift') or p.get('shift')
                pp.intensity = p.get('intensity', 1.0)
                pp.width = p.get('width', 0.0) or p.get('width', 0.0)
                pp.multiplicity = p.get('multiplicity', 's')
                pp.integration = p.get('integration', 1.0)
                pp.coupling_constants = p.get('coupling_constants', [])
                peaks_list.append(pp)
            spectrum.peaks = peaks_list
            print("Export fallback: using last_spectrum_data to construct proxy spectrum for export")
        
        # Create in-memory file for export
        from io import BytesIO, StringIO
        import csv
        
        if format.lower() == 'csv':
            # Export as CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Chemical_Shift_ppm', 'Intensity'])
            
            if spectrum.ppm_axis is not None and spectrum.data_points is not None:
                for ppm, intensity in zip(spectrum.ppm_axis, spectrum.data_points):
                    writer.writerow([f'{ppm:.6f}', f'{intensity:.6f}'])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'nmr_spectrum_{spectrum.nucleus}.csv'
            )
        
        elif format.lower() == 'txt':
            # Export as tab-separated text
            output = StringIO()
            output.write('Chemical_Shift_ppm\tIntensity\n')
            
            if spectrum.ppm_axis is not None and spectrum.data_points is not None:
                for ppm, intensity in zip(spectrum.ppm_axis, spectrum.data_points):
                    output.write(f'{ppm:.6f}\t{intensity:.6f}\n')
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'nmr_spectrum_{spectrum.nucleus}.txt'
            )
        
        elif format.lower() == 'png':
            # Export plot as PNG image
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if spectrum.ppm_axis is not None and spectrum.data_points is not None:
                ax.plot(spectrum.ppm_axis, spectrum.data_points, 'b-', linewidth=1.5)
                ax.set_xlim(spectrum.ppm_range[1], spectrum.ppm_range[0])  # NMR convention
                ax.set_xlabel('Chemical Shift (ppm)', fontsize=12)
                ax.set_ylabel('Intensity', fontsize=12)
                ax.set_title(f'{spectrum.nucleus} NMR Spectrum ({spectrum.field_strength} MHz)', fontsize=14)
                ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            plt.close(fig)
            
            return send_file(
                buffer,
                mimetype='image/png',
                as_attachment=True,
                download_name=f'nmr_spectrum_{spectrum.nucleus}.png'
            )

        elif format.lower() in ('jcamp', 'jdx'):
            # JCAMP-DX export with essential headers for MNova compatibility
            open('C:\\tmp\\jcamp_called.txt', 'a').write('JCAMP export called\n')  # DEBUG
            try:
                if spectrum.ppm_axis is None or spectrum.data_points is None:
                    return jsonify({'error': 'No spectrum data available for JCAMP export'}), 400
                
                x_arr = np.array(spectrum.ppm_axis)
                y_arr = np.array(spectrum.data_points)
                
                # **ENSURE ppm_axis is in ascending order (low→high) for JCAMP**
                x_arr, y_arr = _ensure_ascending_ppm(x_arr, y_arr)
                
                npts = len(x_arr)
                firstx = float(x_arr[0])    # Lowest ppm
                lastx = float(x_arr[-1])     # Highest ppm
                deltax = float((lastx - firstx) / (npts - 1)) if npts > 1 else 0.0  # Positive
                
                print(f"JCAMP: FIRSTX={firstx:.6f}, LASTX={lastx:.6f}, DELTAX={deltax:.9f}, NPOINTS={npts}")
                lines = [
                    '##TITLE= NMR Spectrum',
                    '##JCAMP-DX= 5.01',
                    '##DATA TYPE= NMR SPECTRUM',
                    '##ORIGIN= Generated by web_app',
                    '##OWNER= User',
                    '##XUNITS= PPM',
                    '##YUNITS= ARBITRARY',
                    f'##FIRSTX= {firstx:.6f}',
                    f'##LASTX= {lastx:.6f}',
                    f'##NPOINTS= {npts}',
                    f'##DELTAX= {deltax:.9f}',
                    '##XYDATA= (X++(Y..Y))'
                ]
                for x, y in zip(x_arr, y_arr):
                    lines.append(f'{float(x):.6f} {float(y):.6f}')
                lines.append('##END=')
                payload = '\n'.join(lines)
                return send_file(
                    io.BytesIO(payload.encode('utf-8')),
                    mimetype='chemical/x-jcamp-dx',
                    as_attachment=True,
                    download_name=f'nmr_spectrum_{spectrum.nucleus}.jdx'
                )
            except Exception as je:
                print(f'JCAMP export failed: {je}')
                return jsonify({'error': f'JCAMP export failed: {je}'}), 500

        elif format.lower() == 'bruker':
            # Provide a zip with Bruker folder hierarchy (pdata/1/1r) for Bruker/MNova compatibility
            try:
                import zipfile
                import struct
                mem = io.BytesIO()
                with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # Bruker 1r file (real FID/spectrum data) in proper hierarchy: pdata/1/1r
                    try:
                        if spectrum.data_points is not None and len(spectrum.data_points) > 0:
                            fid_data = struct.pack(f'{len(spectrum.data_points)}i', *[int(y * 1000) for y in spectrum.data_points])
                            zf.writestr('pdata/1/1r', fid_data)
                    except Exception as fid_err:
                        print(f'1r file generation failed: {fid_err}')
                    
                    # Minimal procs file (processing parameters) for Bruker format
                    try:
                        if spectrum.ppm_axis is not None and len(spectrum.ppm_axis) > 0:
                            x_arr = np.array(spectrum.ppm_axis)
                            y_arr = np.array(spectrum.data_points)
                            # **ENSURE ppm_axis is in ascending order (low→high)**
                            x_arr, y_arr = _ensure_ascending_ppm(x_arr, y_arr)
                            
                            # Bruker procs expects OFFSET as starting offset (lowest ppm) and SW_p as positive spectral width
                            offset = float(x_arr[0])      # Lowest ppm value (starting offset)
                            sw_p = float(x_arr[-1] - x_arr[0])  # Spectral width in ppm (positive)
                            sf = float(getattr(spectrum, 'field_strength', 400.0))
                            
                            print(f"Bruker procs: OFFSET={offset:.6f} (lowest ppm), SW_p={sw_p:.6f} (positive), SF={sf:.6f}")
                            
                            procs_content = f"""##TITLE= Parameter file, TOPSPIN Version 3.0
##JCAMPDX= 5.0
##DATATYPE= Parameter Values
##ORIGIN= Bruker BioSpin GmbH
##OWNER= nmr
$$ {os.path.abspath(__file__)}
##$OFFSET= {offset:.6f}
##$SW_p= {sw_p:.6f}
##$SF= {sf:.6f}
##$SI= {len(spectrum.data_points)}
##$MC2= 0
##$PKNL= 1
##END=
"""
                            zf.writestr('pdata/1/procs', procs_content)
                    except Exception as procs_err:
                        print(f'procs file generation failed: {procs_err}')

                    # peaks CSV
                    peaks_buf = io.StringIO()
                    writer = csv.writer(peaks_buf)
                    writer.writerow(['Peak_ID', 'Chemical_Shift_ppm', 'Intensity', 'Width_ppm', 'Multiplicity', 'Integration'])
                    for i, p in enumerate(getattr(spectrum, 'peaks', []) if getattr(spectrum, 'peaks', None) is not None else [] , 1):
                        try:
                            writer.writerow([
                                i,
                                f"{getattr(p, 'chemical_shift', '')}",
                                f"{getattr(p, 'intensity', '')}",
                                f"{getattr(p, 'width', '')}",
                                f"{getattr(p, 'multiplicity', '')}",
                                f"{getattr(p, 'integration', '')}"
                            ])
                        except Exception:
                            continue
                    zf.writestr('peaks.csv', peaks_buf.getvalue())

                    # spectrum CSV
                    spec_buf = io.StringIO()
                    spec_writer = csv.writer(spec_buf)
                    spec_writer.writerow(['Chemical_Shift_ppm', 'Intensity'])
                    if spectrum.ppm_axis is not None and spectrum.data_points is not None:
                        for x, y in zip(spectrum.ppm_axis, spectrum.data_points):
                            spec_writer.writerow([f'{float(x):.6f}', f'{float(y):.6f}'])
                    zf.writestr('spectrum.csv', spec_buf.getvalue())

                mem.seek(0)
                return send_file(
                    mem,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=f'nmr_bruker_export_{spectrum.nucleus}.zip'
                )
            except Exception as be:
                print(f'Bruker export failed: {be}')
                return jsonify({'error': f'Bruker export failed: {be}'}), 500
        
        elif format.lower() == 'peaks':
            # Export peak list as CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Peak_ID', 'Chemical_Shift_ppm', 'Intensity', 'Width_ppm', 'Multiplicity', 'Integration', 'Coupling_Constants_Hz'])
            
            for i, peak in enumerate(spectrum.peaks, 1):
                coupling_str = ', '.join([f'{j:.1f}' for j in peak.coupling_constants]) if peak.coupling_constants else ''
                writer.writerow([
                    i,
                    f'{peak.chemical_shift:.3f}',
                    f'{peak.intensity:.3f}',
                    f'{peak.width:.4f}',
                    peak.multiplicity,
                    f'{peak.integration:.1f}',
                    coupling_str
                ])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'nmr_peaks_{spectrum.nucleus}.csv'
            )
        
        else:
            return jsonify({'error': f'Unsupported export format: {format}. Supported formats: csv, txt, png, peaks, jcamp, bruker'})
            
    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Export failed: {str(e)}'})


@app.route('/get_peaks', methods=['GET'])
def get_peaks():
    """Return the last parsed/generated peaks as JSON for the frontend or API clients.

    Uses `nmr_app.last_spectrum_data` when available (preferred), otherwise falls
    back to `nmr_app.last_spectrum` object.
    """
    try:
        # Prefer structured data stored during generation
        if getattr(nmr_app, 'last_spectrum_data', None):
                data = nmr_app.last_spectrum_data
                peaks = data.get('peaks', [])
                # Ensure each peak has a numeric id for the frontend editor (1-based)
                out_peaks = []
                for i, p in enumerate(peaks):
                    try:
                        npk = dict(p) if isinstance(p, dict) else p.__dict__
                    except Exception:
                        npk = {'chemical_shift': getattr(p, 'chemical_shift', None)}
                    npk['id'] = i + 1
                    out_peaks.append(npk)
                meta = {
                    'nucleus': data.get('nucleus'),
                    'field_strength': data.get('field_strength')
                }
                return jsonify({'peaks': out_peaks, 'metadata': meta}), 200

        # Fallback to last_spectrum object if present
        if getattr(nmr_app, 'last_spectrum', None):
            spec = nmr_app.last_spectrum
            out_peaks = []
            try:
                for p in spec.peaks:
                        out_peaks.append({
                            'id': len(out_peaks) + 1,
                            'chemical_shift': getattr(p, 'chemical_shift', None),
                            'intensity': getattr(p, 'intensity', None),
                            'width': getattr(p, 'width', None),
                            'multiplicity': getattr(p, 'multiplicity', None),
                            'integration': getattr(p, 'integration', None),
                            'coupling_constants': list(getattr(p, 'coupling_constants', []) if getattr(p, 'coupling_constants', None) is not None else []),
                            'visual_assignment': getattr(p, 'visual_assignment', '')
                        })
            except Exception:
                out_peaks = []
            return jsonify({'peaks': out_peaks, 'metadata': {'nucleus': getattr(spec, 'nucleus', None), 'field_strength': getattr(spec, 'field_strength', None)}}), 200

        return jsonify({'error': 'No spectrum available. Run /simulate first.'}), 404
    except Exception as e:
        print(f"get_peaks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'get_peaks failed: {str(e)}'}), 500


@app.route('/update_peaks', methods=['POST'])
def update_peaks():
    """Accept a JSON peak list (or full spectrum dict) and regenerate the spectrum.

    Expected JSON formats:
    - {'peaks': [ { 'shift': ..., 'multiplicity': ..., ... }, ... ], 'nucleus': '1H', 'field_strength': 400}
    - or a full spectrum dict with 'ppm_axis' and 'data_points' (will be used as-is)
    """
    try:
        # Try standard JSON parsing first
        data = request.get_json(silent=True)

        # If no JSON, attempt to parse raw body as JSON (some clients send raw bodies without content-type)
        if data is None:
            raw = request.get_data(as_text=False) or b''
            try:
                if raw:
                    import json as _json
                    text = raw.decode('utf-8', errors='replace')
                    data = _json.loads(text)
                else:
                    data = {}
            except Exception:
                # Try form data (e.g., peaks field containing JSON)
                try:
                    if 'peaks' in request.form:
                        import json as _json
                        data = {'peaks': _json.loads(request.form['peaks'])}
                    else:
                        data = {}
                except Exception:
                    data = {}

        # Debug: print content-type and a short preview of body for diagnostics
        try:
            print(f"update_peaks received Content-Type: {request.content_type}")
            preview = (request.get_data() or b'')[:200]
            print(f"update_peaks raw preview (first 200 bytes): {preview!r}")
        except Exception:
            pass

        peaks = data.get('peaks') if isinstance(data, dict) else None
        # Support edit-style payloads with a 'changes' mapping
        changes = data.get('changes') if isinstance(data, dict) else None
        if changes and getattr(nmr_app, 'last_spectrum_data', None):
            stored = nmr_app.last_spectrum_data
            stored_peaks = stored.get('peaks', [])
            for key, mods in (changes.items() if isinstance(changes, dict) else []):
                applied = False
                # Try numeric key -> index
                try:
                    ik = int(key)
                    # try 1-based then 0-based
                    idx = ik - 1 if 0 <= ik - 1 < len(stored_peaks) else (ik if 0 <= ik < len(stored_peaks) else None)
                except Exception:
                    idx = None

                if idx is not None:
                    for k, v in (mods.items() if isinstance(mods, dict) else []):
                        stored_peaks[idx][k] = v
                    applied = True
                else:
                    # If mods contain a chemical_shift, match by nearest shift
                    if isinstance(mods, dict) and 'chemical_shift' in mods:
                        try:
                            target = float(mods['chemical_shift'])
                            best_i = None
                            best_d = float('inf')
                            for i, sp in enumerate(stored_peaks):
                                s = sp.get('chemical_shift') or sp.get('shift')
                                try:
                                    sd = float(s)
                                except Exception:
                                    continue
                                d = abs(sd - target)
                                if d < best_d:
                                    best_d = d
                                    best_i = i
                            if best_i is not None:
                                for k, v in (mods.items() if isinstance(mods, dict) else []):
                                    stored_peaks[best_i][k] = v
                                applied = True
                        except Exception:
                            pass

                # If still not applied, apply to first peak as a best-effort (handles 'undefined' keys)
                if not applied and len(stored_peaks) >= 1:
                    for k, v in (mods.items() if isinstance(mods, dict) else []):
                        stored_peaks[0][k] = v
                    applied = True

            # Save back and use as spec_dict for regeneration
            stored['peaks'] = stored_peaks
            nmr_app.last_spectrum_data = stored
            peaks = stored_peaks
            try:
                print(f"Applied changes to stored_peaks; preview first peak: {stored_peaks[0] if stored_peaks else None}")
            except Exception:
                pass
        if not peaks and 'ppm_axis' not in (data or {}):
            return jsonify({'error': 'No peaks provided in JSON body. Expected JSON like {"peaks":[{...}], "nucleus":"1H"}'}), 400

        # If a full spectrum dict was provided, store and attempt to regenerate plot
        if 'ppm_axis' in data or 'data_points' in data:
            nmr_app.last_spectrum_data = data
            plot_result, groups = nmr_app.generate_spectrum_plot_from_data(data)
        else:
            # Build a minimal spectrum dict for the compatibility wrapper
            spec_dict = {
                'nucleus': data.get('nucleus', '1H'),
                'field_strength': data.get('field_strength', 400),
                'peaks': peaks
            }
            nmr_app.last_spectrum_data = spec_dict
            plot_result, groups = nmr_app.generate_spectrum_plot_from_data(spec_dict)

        if plot_result is None:
            return jsonify({'error': 'Failed to regenerate spectrum.'}), 500

        # Return the regenerated plot (interactive or static) so frontend can update display
        response_payload = {
            'status': 'ok',
            'multiplet_groups': groups,
            'peaks_count': len(peaks) if peaks else len(nmr_app.last_spectrum_data.get('peaks', []))
        }
        try:
            response_payload['plot_data'] = plot_result.get('plot_data')
            response_payload['static_url'] = plot_result.get('static_url')
            response_payload['plot_type'] = plot_result.get('plot_type')
        except Exception:
            pass

        return jsonify(response_payload), 200
    except Exception as e:
        print(f"update_peaks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'update_peaks failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting NMR Spectra Simulator Web Application...")
    print("Open your browser and go to: http://localhost:5000")
    # Run without the auto-reloader to keep in-memory edits persistent during development
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
