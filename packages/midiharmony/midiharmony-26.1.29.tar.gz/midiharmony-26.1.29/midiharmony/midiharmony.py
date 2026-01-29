#! /usr/bin/python3

r'''###############################################################################
###################################################################################
#
#
#	midiharmony Python module
#	Version 1.0
#
#	Project Los Angeles
#
#	Tegridy Code 2026
#
#   https://github.com/Tegridy-Code/Project-Los-Angeles
#
#
###################################################################################
###################################################################################
#
#   Copyright 2026 Project Los Angeles / Tegridy Code
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
###################################################################################
###################################################################################
#
#   Critical dependencies
#
#   !pip install cupy-cuda12x
#   !pip install matplotlib
#   !pip install numpy==1.26.4
#   !pip install tqdm
#
###################################################################################
'''

###################################################################################
###################################################################################

print('=' * 70)
print('Loading midiharmony Python module...')
print('Please wait...')
print('=' * 70)

__version__ = '1.0.0'

print('midiharmony module version', __version__)
print('=' * 70)

###################################################################################
###################################################################################

import os, copy, time

import tqdm

###################################################################################

from . import TMIDIX

from .helpers import get_package_data

###################################################################################

try:
    import cupy as cp
    
    print('CuPy is loaded!')
    
    CUPY_AVAILABLE = True
    
except ImportError:
    
    print('Could not load CuPy!')
    
    CUPY_AVAILABLE = False

import numpy as np

###################################################################################
###################################################################################

def find_quads_fast_cupy(src_array, trg_array, seed: int = 0) -> int:
    
    """
    Count how many rows in src_array also appear in trg_array using CuPy (GPU).
    Uses a non-linear 64-bit FNV-1a hash over raw bytes to avoid collisions.
    """

    src = cp.ascontiguousarray(cp.asarray(src_array))
    trg = cp.ascontiguousarray(cp.asarray(trg_array))

    if src.dtype != trg.dtype or src.ndim != 2 or trg.ndim != 2 or src.shape[1] != trg.shape[1]:
        raise ValueError("src and trg must be 2D arrays with same dtype and same number of columns")

    # bytes per row
    bpr = src.dtype.itemsize * src.shape[1]

    # view rows as bytes
    src_bytes = src.view(cp.uint8).reshape(src.shape[0], bpr)
    trg_bytes = trg.view(cp.uint8).reshape(trg.shape[0], bpr)

    # FNV-1a constants
    FNV_OFFSET = cp.uint64(0xcbf29ce484222325 ^ seed)
    FNV_PRIME  = cp.uint64(0x100000001b3)

    # hash rows
    def fnv1a_hash(byte_matrix):
        h = cp.full((byte_matrix.shape[0],), FNV_OFFSET, dtype=cp.uint64)
        for i in range(bpr):
            h ^= byte_matrix[:, i].astype(cp.uint64)
            h *= FNV_PRIME
        return h

    src_fp = fnv1a_hash(src_bytes)
    trg_fp = fnv1a_hash(trg_bytes)

    # count matches
    return int(cp.isin(src_fp, trg_fp).sum())

###################################################################################

def find_quads_fast_numpy(src_array: np.ndarray, trg_array: np.ndarray) -> int:
    
    """
    Count how many rows in src_array also appear in trg_array using NumPy (CPU).
    """   
    
    # ensure contiguous memory and same dtype
    src = np.ascontiguousarray(src_array)
    trg = np.ascontiguousarray(trg_array)
    if src.dtype != trg.dtype or src.shape[1] != trg.shape[1]:
        raise ValueError("src and trg must have same dtype and same number of columns")

    # view each row as a single fixed-size byte string
    row_dtype = np.dtype((np.void, src.dtype.itemsize * src.shape[1]))
    src_keys = src.view(row_dtype).ravel()
    trg_keys = trg.view(row_dtype).ravel()

    # count how many src rows appear in trg
    return int(np.isin(src_keys, trg_keys).sum())

###################################################################################

_trg_cache_np = None
_trg_cache_cp = None

def get_trg_array(use_gpu: bool = False, verbose: bool = True):
    
    """
    Load and cache the target harmonic‑chord array in either NumPy (CPU) or CuPy (GPU) form.

    Parameters
    ----------
    use_gpu : bool, optional
        If True, return a cached CuPy array; otherwise return a cached NumPy array.
        Falls back to NumPy automatically if CuPy is unavailable.
    verbose : bool, optional
        If True, print diagnostic messages when loading arrays for the first time.

    Returns
    -------
    numpy.ndarray or cupy.ndarray
        The cached target array, loaded once and reused across calls.
    """

    global _trg_cache_np, _trg_cache_cp

    if not use_gpu:
        if _trg_cache_np is None:
            if verbose:
                print("Loading trg array (NumPy)...")
            
            _trg_cache_np = np.load(get_package_data()[0]['path'])['harmonic_chords_quads']
            
        return _trg_cache_np

    # GPU path
    try:
        import cupy as cp
        
    except Exception:
        return get_trg_array(use_gpu=False)

    if _trg_cache_cp is None:
        if verbose:
            print("Loading trg array (CuPy)...")
        
        _trg_cache_cp = cp.asarray(get_trg_array(use_gpu=False,
                                                 verbose=False
                                                ),
                                   dtype=cp.int16
                                  )
        
    return _trg_cache_cp

###################################################################################

def process_midi(midi_file_path: str, verbose: bool = True):
    
    """
    Analyze a MIDI file and extract harmonic information, chord statistics,
    and unique 4‑chord progression quads.

    Parameters
    ----------
    midi_file_path : str
        Path to the MIDI file to process.
    verbose : bool, optional
        If True, print progress messages and execution timing.

    Returns
    -------
    dict
        A dictionary containing:
        
        - 'midi_path' : str  
            Original file path.
        - 'midi_name' : str  
            File name without extension.
        - 'total_chords_count' : int  
            Number of chordified events.
        - 'bad_chords_count' : int  
            Number of chords that required correction.
        - 'grouped_chords_count' : int  
            Length of the grouped chord sequence.
        - 'total_quads_count' : int  
            Total number of extracted 4‑chord windows.
        - 'unique_quads_count' : int  
            Number of unique 4‑chord quads.
        - 'quads' : list[tuple[int]]  
            Unique 4‑chord progressions discovered.

        Returns an empty dictionary if the MIDI contains no events,
        only drums, or an exception occurs.
    """

    midi_name = os.path.splitext(os.path.basename(midi_file_path))[0]

    if verbose:

        start_time = time.time()
        
        print('=' * 70)
        print('Processing', midi_name)

    return_dict = {}

    try:

        raw_score = TMIDIX.midi2single_track_ms_score(midi_file_path,
                                                      do_not_check_MIDI_signature=True,
                                                      verbose=verbose
                                                     )
        
        escore_notes = TMIDIX.advanced_score_processor(raw_score, return_enhanced_score_notes=True)

        # ==================================================================================

        if escore_notes and escore_notes[0]:

            escore_notes = TMIDIX.strip_drums_from_escore_notes(escore_notes[0])

            if escore_notes:
        
                escore_notes = TMIDIX.augment_enhanced_score_notes(escore_notes)
                
                cscore = TMIDIX.chordify_score([1000, escore_notes])
    
                # ==================================================================================
        
                chords = []
    
                bchords = 0
            
                for c in cscore:
                    tones_chord = sorted(set([e[4] % 12 for e in c]))
                    
                    if tones_chord not in TMIDIX.ALL_CHORDS_SORTED:
                        tones_chord = TMIDIX.check_and_fix_tones_chord(tones_chord,
                                                                       use_full_chords=False
                                                                      )
    
                        bchords += 1
    
                    chord_tok = TMIDIX.ALL_CHORDS_SORTED.index(tones_chord)
                
                    chords.append(chord_tok)
    
                # ==================================================================================
        
                gchords = TMIDIX.grouped_set(chords)
    
                # ==================================================================================
    
                quads = set()
                
                qcount = 0
    
                for i in range(len(gchords)):
                    quad = gchords[i:i+4]
                
                    if len(quad) == 4:
                        quads.add(tuple(quad))
                        qcount += 1
    
                    else:
                        last_quad = gchords[-4:]
    
                        if len(last_quad) == 4:
                            quads.add(tuple(last_quad))
                            qcount += 1
    
                quads = list(quads)
    
                # ==================================================================================

                return_dict['midi_path'] = midi_file_path
                return_dict['midi_name'] = midi_name
                
                return_dict['total_chords_count'] = len(cscore)
                return_dict['bad_chords_count'] = bchords
                return_dict['grouped_chords_count'] = len(gchords)
                
                return_dict['total_quads_count'] = qcount
                return_dict['unique_quads_count'] = len(quads)
                return_dict['quads'] = quads
    
                # ==================================================================================

                if verbose:
                    print('Done!')
                    print('=' * 70)

                    end_time = time.time()

                    execution_time = end_time - start_time

                    print(f"Execution time: {execution_time:.4f} seconds")
                    print('=' * 70)
        
                return return_dict

            else:
                if verbose:
                    print('MIDI is a drum track without chords!')
                    print('=' * 70)
                    
                    end_time = time.time()

                    execution_time = end_time - start_time

                    print(f"Execution time: {execution_time:.4f} seconds")
                    print('=' * 70)
                    
                return return_dict

        else:
            if verbose:
                print('MIDI does not appear to have any events!')
                print('=' * 70)
                
                end_time = time.time()

                execution_time = end_time - start_time

                print(f"Execution time: {execution_time:.4f} seconds")
                print('=' * 70)
                
            return return_dict

    except Exception as ex:

        if verbose:
            print('WARNING !!!')
            print('=' * 70)
            print(f)
            print('=' * 70)
            print('Error detected:', ex)
            print('=' * 70)

            end_time = time.time()

            execution_time = end_time - start_time

            print(f"Execution time: {execution_time:.4f} seconds")
            print('=' * 70)

        return return_dict

###################################################################################

def analyze_processed_midi(processed_midi_dict,
                           keep_quads: bool = False,
                           verbose: bool = False
                          ):
    
    """
    Evaluate harmonic quality of a processed MIDI file by comparing its
    extracted chord‑quad sequences against the target quad database.

    Parameters
    ----------
    processed_midi_dict : dict
        Output dictionary from `process_midi`, containing extracted chord
        information and a 'quads' list of 4‑chord progressions.
    keep_quads : bool, optional
        If True, preserve the original 'quads' list in the returned dictionary.
        If False, omit it to reduce memory usage.
    verbose : bool, optional
        If True, print progress messages and timing information.

    Returns
    -------
    dict
        A dictionary containing the original processed‑MIDI metadata plus:
        
        - 'harmonic_quads_count' : int  
            Number of quads that match entries in the target quad database.
        - 'harmony_ratio' : float  
            Fraction of matching quads relative to total quads.

        If `keep_quads` is False, the 'quads' key is removed.
    """

    if verbose:

        start_time = time.time()
        
        print('=' * 70)
        print('Analyzing harmony...')
        print('=' * 70)

    if verbose:
        print('Prepping src_array...')

    if CUPY_AVAILABLE:
        src_array = cp.asarray(processed_midi_dict['quads'], dtype=cp.int16)

    else:
        src_array = np.asarray(processed_midi_dict['quads'], dtype=np.int16)
   
    trg_array = get_trg_array(CUPY_AVAILABLE, verbose=verbose) 
    
    if verbose:
        print('Processing...')

    res = 0
    src_array_len = max(1, src_array.shape[0])

    if CUPY_AVAILABLE:
        if verbose:
            print('Using CuPy / GPU...')
            
        res = find_quads_fast_cupy(src_array, trg_array)

    else:

        if verbose:
            print('Using NumPy / CPU...')
            
        res = find_quads_fast_numpy(src_array, trg_array)

    if keep_quads:
        harmony_dict = copy.deepcopy(processed_midi_dict)

    else:
        harmony_dict = {k: v for k, v in processed_midi_dict.items() if k != 'quads'}

    harmony_dict['harmonic_quads_count'] = res
    harmony_dict['harmony_ratio'] = res / src_array_len

    if verbose:

        print('Done!')
        print('=' * 70)

        end_time = time.time()

        execution_time = end_time - start_time
    
        print(f"Execution time: {execution_time:.4f} seconds")
        print('=' * 70)

    return harmony_dict

###################################################################################

def analyze_midi(midi_file_path: str, verbose: bool = True):
    
    """
    End‑to‑end MIDI harmony analysis pipeline combining chord extraction
    and harmonic‑quad evaluation.

    Parameters
    ----------
    midi_file_path : str
        Path to the MIDI file to analyze.
    verbose : bool, optional
        If True, print progress messages and total execution time.

    Returns
    -------
    dict
        The harmony‑analysis dictionary produced by `analyze_processed_midi`.
        Returns an empty dictionary if processing fails or the MIDI contains
        no analyzable harmonic content.
    """

    processed_midi_dict = {}
    harmony_dict = {}

    if verbose:
        start_time = time.time()

    processed_midi_dict = process_midi(midi_file_path,
                                       verbose=verbose
                                      )

    if processed_midi_dict:
        harmony_dict = analyze_processed_midi(processed_midi_dict,
                                              verbose=verbose
                                             )

    if verbose:

        end_time = time.time()

        execution_time = end_time - start_time
    
        print(f"Total execution time: {execution_time:.4f} seconds")
        print('=' * 70)

    return harmony_dict
    
###################################################################################

def analyze_midi_folders(midi_folders_paths_list,
                         midi_files_extensions=['.mid', '.midi', '.kar'],
                         show_progress_bar: bool = True,
                         verbose: bool = False
                        ):
    
    """
    Batch‑analyze all MIDI files inside one or more folders, producing
    harmony‑analysis dictionaries for each valid file.

    Parameters
    ----------
    midi_folders_paths_list : list[str]
        List of folder paths to search for MIDI files.
    midi_files_extensions : list[str], optional
        File extensions to include when scanning folders.
    show_progress_bar : bool, optional
        If True, display a tqdm progress bar while processing files.
    verbose : bool, optional
        If True, print diagnostic information and timing details.

    Returns
    -------
    list[dict]
        A list of harmony‑analysis dictionaries, one per successfully
        processed MIDI file. Files that fail processing or contain no
        analyzable harmonic content are skipped.
    """

    if verbose:
        start_time = time.time()
        
        print('=' * 70)
        print('Processing MIDI folders:', midi_folders_paths_list)

    midi_files_list = TMIDIX.create_files_list(midi_folders_paths_list,
                                               files_exts=midi_files_extensions,
                                               verbose=verbose
                                              )

    all_harmony_dicts_list = []

    for midi_file in tqdm.tqdm(midi_files_list,
                               desc='Processing MIDIs',
                               unit='file',
                               disable=not show_progress_bar
                              ):
        

        processed_midi_dict = {}
        harmony_dict = {}
    
        processed_midi_dict = process_midi(midi_file,
                                           verbose=verbose
                                          )
    
        if processed_midi_dict:
            harmony_dict = analyze_processed_midi(processed_midi_dict,
                                                  verbose=verbose
                                                 )

            all_harmony_dicts_list.append(harmony_dict)

    if verbose:

        print('Done!')
        print('=' * 70)
        print('Total number of input MIDIs:', len(midi_files_list))
        print('Total number of output MIDIs:', len(all_harmony_dicts_list))
        print('Good / bad ratio:', len(all_harmony_dicts_list) / max(1, len(midi_files_list)))
        print('=' * 70)
        
        end_time = time.time()

        execution_time = end_time - start_time
    
        print(f"Total execution time: {execution_time:.4f} seconds")
        print('=' * 70)

    return all_harmony_dicts_list

###################################################################################

print('Module is loaded!')
print('Enjoy! :)')
print('=' * 70)

###################################################################################
# This is the end of the midiharmony Python module
###################################################################################