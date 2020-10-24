# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
import time
import pickle
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
from keras.utils import to_categorical
from music21 import instrument, note, chord, stream
from pathlib import Path
import os

@blueprint.route('/index')
@login_required
def index():

    return render_template('index.html')

@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith( '.html' ):
            template += '.html'

        return render_template( template )

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500


# model paths
composers_dict = {'albeniz':'''.\\models\\model_albeniz.hdf5''',
'beeth':'''.\\models\\model_beeth.hdf5''',
'chopin':'''.\\models\\model_chopin.hdf5''',
'haydn':'''.\\models\\model_haydn.hdf5''',
'mozart':'''.\\models\\model_mozart.hdf5'''}

model_albeniz = tf.keras.models.load_model(composers_dict['albeniz'])
model_beeth = tf.keras.models.load_model(composers_dict['beeth'])
model_chopin = tf.keras.models.load_model(composers_dict['chopin'])
model_haydn = tf.keras.models.load_model(composers_dict['haydn'])
model_mozart = tf.keras.models.load_model(composers_dict['mozart'])

composers_model = {'albeniz': model_albeniz, 'beeth': model_beeth, 'chopin': model_chopin,
 'haydn': model_haydn, 'mozart': model_mozart}

def get_notes(composer):
    notes = []
    with open(Path('''.\\notes\\notes_%s''' % (composer)), 'rb') as filepath:
        notes = pickle.load(filepath)
    n_vocab = len(sorted(list(set(notes))))
    pitchnames = sorted(list(set(notes)))
    return notes, n_vocab, pitchnames

def prepare_sequences(notes, n_vocab, pitchnames):
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    sequence_length = 40
    network_input = []
    # network_output = []
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        # sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
        # network_output.append(note_to_int[sequence_out])

    n_patterns = len(network_input)

    # reshape the input into a format compatible with LSTM layers
    network_input = np.reshape(network_input, (n_patterns, sequence_length, 1))
    # network_output = to_categorical(network_output)

    return network_input

def generate_notes(composer, network_input, pitchnames, n_vocab):
    # pick a random sequence from the input as a starting point for the prediction
    start = np.random.randint(0, len(network_input)-1)

    int_to_note = dict((number, note) for number, note in enumerate(pitchnames))
    # note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    pattern = network_input[start]
    prediction_output = []

    for i in range(50):
        prediction_input = np.reshape(pattern, (1, len(pattern), 1))
        if composer == 'beeth':
            prediction_input = prediction_input / float(n_vocab)
        
        prediction = composers_model[composer].predict(prediction_input, verbose=0)

        index = np.argmax(prediction)
        result = int_to_note[index]
        prediction_output.append(result)

        pattern = np.append(pattern, index)
        pattern = pattern[1:]

    return prediction_output

def generate_notes_from_keyboard(input_from_keyboard, composer, pitchnames, n_vocab):
    max_sequence_len = 40
    input_from_keyboard = input_from_keyboard.split() #input note characters

    int_to_note = dict((number, note) for number, note in enumerate(pitchnames))
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    to_index = []
    for char in input_from_keyboard:
        to_index.append(note_to_int[char])
    to_index = np.array(pad_sequences([to_index], maxlen=max_sequence_len, padding='pre'))

    output_from_keyboard = input_from_keyboard.copy()

    for i in range(55):
        prediction_input = np.reshape(to_index, (1, max_sequence_len, 1))
        if composer == 'beeth':
            prediction_input = prediction_input / float(n_vocab)

        prediction = composers_model[composer].predict(prediction_input, verbose=0)

        index = np.argmax(prediction)
        result = int_to_note[index]
        output_from_keyboard = np.append(output_from_keyboard, result)

        to_index = np.append(to_index, index)
        to_index = to_index[1:]
    
    return output_from_keyboard

def create_midi(composer, prediction_output, file_name):
    offset = 0
    output_notes = []

    print(prediction_output)

    # create note and chord objects based on the values generated by the model
    for pattern in prediction_output:
        # pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                # new_note.storedInstrument = instrument.Flute()
                notes.append(new_note)
            output_notes.append(instrument.Piano())
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        elif pattern == 'rest':
            output_notes.append(instrument.Piano())
            new_note = note.Rest()
            new_note.offset = offset
            # new_note.storedInstrument = instrument.Flute()
            output_notes.append(new_note)
        # pattern is a note
        else:
            output_notes.append(instrument.Piano())
            new_note = note.Note(pattern)
            new_note.offset = offset
            # new_note.storedInstrument = instrument.Flute()
            output_notes.append(new_note)

        offset += 0.5

    midi_stream = stream.Stream(output_notes)

    midi_stream.write('midi', file_name)


@blueprint.route('/predict/', methods=["POST"])
def predict():
    data = request.get_json()

    # Preprocess
    input_from_keyboard = data['data-uri'] 
    composer = data['composer']
    print("Input Notes", input_from_keyboard)
    print("Composer", composer)
    
    notes, n_vocab, pitchnames = get_notes(composer)
    # print(len(notes))
    network_input = prepare_sequences(notes, n_vocab, pitchnames)
    
    if input_from_keyboard:
        output_notes = generate_notes_from_keyboard(input_from_keyboard, composer, pitchnames, n_vocab)
    else:
        output_notes = generate_notes(composer, network_input, pitchnames, n_vocab)
        
    file_name= '''{}{}.mid'''.format(composer, int(time.time()))
    path_system = '''.\\app\\base\\static\\audio\\''' + file_name
    print(path_system)
    path_browser = '''/static/audio/''' + file_name
    print(path_browser)
    create_midi(composer, output_notes, path_system)

    # file_name = 'static/audio/beeth_1.mid'
    return jsonify({'audio_filename': path_browser})