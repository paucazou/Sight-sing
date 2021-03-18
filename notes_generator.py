#!/usr/bin/python3
# -*-coding:Utf-8 -*
#Deus, in adjutorium meum intende

import mingus.containers.note as mcn
import mingus.core.intervals as mci
import mingus.core.scales as mcs
import random

DEGREES = "I II III IV V VI VII".split()


class Node:
    """Represents one note followed
    by another one or at the end"""
    def __init__(self, note):
        self.note = note
        self.child = None
        self.has_end = False

    def __repr__(self):
        return f"N{self.note} {self.child if self.child else ''}"

    def __eq__(self, other):
        return self.note == other.note and self.child == other.child

    def __hash__(self):
        return hash((self.note.octave,self.note.name,self.child))

    def __iter__(self):
        yield self.note
        if self.child is not None:
            yield from self.child


class NotesGenerator:
    """Generates a tree of nodes"""
    def __init__(self, selector, end):
        self.selector = selector
        self.end = end

        # intervals random balance
        # weight is the following: 10*index + 1
        # Change this parameter to balance the weight of each interval
        self.intervals_balance = {
                itvl : 10*i+1 for i, itvl in enumerate(self.selector.config.interval_priority)
                }

    def shuffle(self, seq, previous):
        """Suffle seq and return a new sequence
        Balance between intervals is applied."""
        weights = {}

        for elt in seq:
            pn, en = previous.note.name, elt.note.name
            n1, n2 = (pn, en) if previous.note < elt.note else (en, pn)
            #self.weights.append(self.intervals_balance[mci.determine(n1,n2,True)])
            itvl = mci.determine(n1,n2,True)[-1]
            weights[elt] = self.intervals_balance[int(itvl)]

        shuffled_seq = []
        while len(weights) > 0:
            selected = random.choices(list(weights.keys()),tuple(weights.values()))[0]
            shuffled_seq.append(selected)
            del(weights[selected])

        return shuffled_seq

    def _generate_children(self, previous, level):
        if level == self.end:
            previous.has_end = True
            return previous

        previous_note = previous.note if previous is not None else None
        children = self.selector(level, self.end, previous_note)
        if previous is not None:
            children = self.shuffle(children, previous) 
        else:
            random.shuffle(children)

        for c in children:
            if c.child is None: # the selector can return a child which already has a child, especially in schemes
                self._generate_children(c, level + 1)
            if c.has_end:
                if previous is None:
                    return c
                previous.child = c
                previous.has_end = True
                return previous
        return previous

    def __call__(self):
        self.selector.setup()
        self.start = self._generate_children(None,0)

        return self.start

class NotesSelector:
    """Select notes following rules and context"""
    def __init__(self, config):
        self.config = config
        self.setup()

    def setup(self):
        """Set up the main features"""
        # scale
        self.tonic = tonic = self.config.scale
        self.is_minor = not tonic[0].isupper()
        self.scale = [mcs.NaturalMinor(tonic.upper()) , mcs.MelodicMinor(tonic.upper())] if self.is_minor else mcs.Major(tonic.upper())

        # last notes
        self.last_degrees = self.last_degrees_possible = [degrees.split(',') for degrees in self.config.last_degrees]
        self.first_last_note_pos = self.config.number - max(
                [len(seq) for seq in self.last_degrees]
                )
        self.last_notes_found = []
        self._generate_last_notes()
        self.previous_last_notes = []

    def _generate_last_notes(self):
        self.last_notes = [
                [self.scale.degree(DEGREES.index(d)+1) for d in degrees]
                for degrees in self.last_degrees_possible
                ]

    def find_degree(self, note):
        if isinstance(note,mcn.Note):
            note = note.name
        if self.is_minor:
            if note in self.scale[0]:
                return self.scale[0].ascending().index(note) + 1
            return self.scale[1].ascending().index(note) + 1
        return self.scale.ascending().index(note) + 1

    def from_one_note(self,note):
        """Return a list of nodes
        matching the rules that can be found from one note"""
        note_degree = self.find_degree(note)
        intervals_available = self.config.degrees[DEGREES[note_degree-1]]
        intervals_available = [itvl - 1 for itvl in intervals_available]
        intervals_available += [-itvl for itvl in intervals_available]
        notes = []
        for itvl in intervals_available:
            res = mci.interval(self.tonic,note.name,itvl)
            # check degree
            if self.find_degree(res) not in self.config.degrees_available:
                continue
            # find the correct octave
            new_note = mcn.Note(res,note.octave)
            if itvl < 0 and new_note > note:
                new_note.octave_down()
            elif itvl > 0 and new_note < note:
                new_note.octave_up()
            elif itvl != 0 and itvl%7 == 0:
                # octave special case
                fun = [new_note.octave_down,new_note.octave_up][itvl>0]
                itvl_ = abs(itvl)
                while itvl_ > 0:
                    fun()
                    itvl_ -= 7

            # check tessitura
            if not (self.config.tessitura[0] <= new_note <= self.config.tessitura[1]):
                continue
            new_note = Node(new_note)
            if new_note not in notes:
                notes.append(new_note)
        return notes


    def find_first_note(self):
        """Find the first note of the melody"""
        # TODO MINOR NOT SET
        starting_notes = [self.scale.degree(DEGREES.index(d)+1) for d in self.config.first_degree]

        possible_start = []
        for sn in starting_notes:
            new_note = mcn.Note(sn,self.config.tessitura[0].octave)
            while new_note <= self.config.tessitura[1]:
                if new_note < self.config.tessitura[0]:
                    new_note.octave_up()
                    continue
                possible_start.append(Node(new_note))
                new_note = mcn.Note(sn,new_note.octave + 1)
        return possible_start

    def check_tessitura(self, note):
        """
        True if note is in tessitura
        """
        return self.config.tessitura[0] <= note <= self.config.tessitura[1]

    def find_last_note(self,parent, notes, degrees, returned_notes):
        """Find one of the last note
        Recursive function"""
        # TODO dans le cas d'une succession comme V-I, le saut de quarte est aussi bon que le saut de quinte. Sélectionner aléatoirement ?
        new_note = notes[0]
        parent_note = parent
        parent_degree = self.find_degree(parent_note)
        par_octave = parent_note.octave

        possible_notes = [mcn.Note(new_note,octave) for octave in (par_octave -1, par_octave, par_octave + 1)]
        possible_notes_semitones = {abs(parent_note.measure(n)):n for n in possible_notes}

        find_interval = lambda x,y : int(mci.determine(x,y,True)[-1])
        interval1 = find_interval(new_note,parent_note.name)
        interval2 = find_interval(parent_note.name,new_note)
        lower,greater = (interval1,interval2) if interval1 < interval2 else (interval2, interval1)
        selected_note = None
        if lower in self.config.degrees_numeric[parent_degree]:
            possible_min = min(possible_notes_semitones.keys())
            selected_note = possible_notes_semitones[possible_min]
            if not (self.check_tessitura(selected_note)):
                selected_note = None
                del(possible_notes_semitones[possible_min])


        if selected_note is None:
            if greater in self.config.degrees_numeric[parent_degree]:
                # we must take here the minimum, since the max possible would be too large
                selected_note = possible_notes_semitones[min(possible_notes_semitones.keys())]
                if not (self.check_tessitura(selected_note)):
                    selected_note = None
            else:
                return returned_notes

        returned_notes.append(Node(selected_note))

        if len(notes) > 1:
            return self.find_last_note(selected_note, notes[1:], degrees[1:],returned_notes)
        return returned_notes 

    def __call__(self, pos, end, parent=None):
        # check position
        if pos == 0:
            return self.find_first_note()


        if pos >= self.first_last_note_pos and len(self.last_notes_found) == 0:
            # if length of the schemes is not the same, select either a scheme of a particular length and suppress the other length schemes, either a random note, and suppress the schemes of the greater length
            lengths = [len(scheme) for scheme in self.last_degrees_possible]
            if min(lengths) == max(lengths):
                self.last_notes_found = [self.find_last_note(parent, notes,degrees,[]) for notes,degrees in zip(self.last_notes, self.last_degrees_possible)]
            # if not, select a scheme or a random note
            elif random.randint(0,len(self.last_degrees_possible)) == 1:
                # select scheme
                # delete schemes that are now too short
                self.last_degrees_possible = [elt for elt in self.last_degrees_possible if len(elt) == max(lengths)]
                self._generate_last_notes()
                self.last_notes_found = [self.find_last_note(parent, notes,degrees,[]) for notes,degrees in zip(self.last_notes, self.last_degrees_possible)]
                # if no scheme matches the rules, the end of the function will return a random note

            else:
                # we need to delete schemes that are now too long
                self.last_degrees_possible = [elt for elt in self.last_degrees_possible if len(elt) != max(lengths)]
                self._generate_last_notes()

            # delete lists that don't contain notes because no one is found
            self.last_notes_found = [l for l in self.last_notes_found if l]

        if self.last_notes_found:
            notes = []
            for l in self.last_notes_found:
                if l:
                    notes.append(l.pop(0))
                else:
                    notes.append(None)

            if self.previous_last_notes:
                # check that the list of notes match the previous notes, if necessary
                temp_notes = notes
                notes = []
                for old, new in zip (self.previous_last_notes, temp_notes):
                    if None is old or None is new:
                        notes.append(None)
                    elif old.note == parent:
                        notes.append(new)
                    else:
                        notes.append(None)

            self.previous_last_notes = notes


            if len(self.last_notes_found) == 0:
                self.last_degrees_possible = self.last_degrees
                self._generate_last_notes()
                self.previous_last_notes = []
            return [n for n in notes if n is not None]



        return self.from_one_note(parent)

