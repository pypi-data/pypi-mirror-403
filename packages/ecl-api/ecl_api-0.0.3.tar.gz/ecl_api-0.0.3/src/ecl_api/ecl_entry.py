'''
Contains code to talk to the ECL API
'''
import os
import base64
import xml.etree.ElementTree as ET


class ECLEntry:
    '''
    A class representing a single ECL entry
    '''
    #pylint: disable=invalid-name,too-many-arguments

    def __init__(self, category, tags=(), formname='default', text='', preformatted=False,
                private=False, related_entry=None):

        '''
        Contructor
        '''

        self._category = category
        self._tags = tags
        self._formname = formname
        self._text = text

        # Create the top level element
        self._entry = ET.Element('entry', category=category)

        if not preformatted:
            self._entry.attrib['formatted']='formatted'
        else:
            self._entry.attrib['formatted']='no'

        if private:
            self._entry.attrib['private'] = 'yes'
        else:
            self._entry.attrib['private'] = 'no'

        if related_entry:
            self._entry.attrib['related'] = str(related_entry)


        # Create the form
        self._form = ET.SubElement(self._entry, 'form', name=formname)
        if text:
            # Create the text field
            textfield = ET.SubElement(self._form, 'field', name='text')
            # Store the text
            textfield.text = text
        for tag in tags:
            ET.SubElement(self._entry, 'tag', name=tag)

    def set_value(self, name, value):
        '''
        Sets a single value to the entry form
        '''

        field = ET.SubElement(self._form, 'field', name=name)
        field.text = value

    def set_author(self, name):
        '''
        Sets the author
        '''
        self._entry.attrib['author'] = name

    def set_form_elements(self, form):
        '''
        Sets a form

        Args:
            form (dict): A dictionary containing the form
        '''
        for name, value in form.items():
            formitem = ET.SubElement(self._form, 'field', name=name)
            formitem.text = value


    def add_attachment(self, name, filename, data=None):
        '''
        Adds a generic file attachment
        '''

        field = ET.SubElement(self._entry, 'attachment', type='file',
            name=name, filename=os.path.basename(filename))

        if data:
            field.text = base64.b64encode(data)
        else:
            with open(filename, 'rb') as file:
                base64_bytes = base64.b64encode(file.read())
                field.text = str(base64_bytes)


    def add_image(self, name, filename, image=None, caption=''):
        '''
        Adds an image attachment
        '''

        field = ET.SubElement(self._entry, 'attachment', type='image',
            name=name, filename=os.path.basename(filename), caption=caption)

        if image:
            field.text = base64.b64encode(image)
        else:
            with open(filename, 'rb') as image_file:
                base64_bytes = base64.b64encode(image_file.read())
                field.text = base64_bytes.decode('UTF-8')

    def show(self, pretty=False):
        '''
        Returns the entry in str format

        Args:
            pretty (bool): If True, adds indentations
        '''

        def indent(elem, level=0):
            '''
            Indents xml text
            '''
            i = "\n" + level*"  "
            j = "\n" + (level-1)*"  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for subelem in elem:
                    indent(subelem, level+1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = j
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = j
            return elem

        if pretty:
            # ET.indent(self._entry)
            indent(self._entry)
        return ET.tostring(self._entry).decode('UTF-8')
