# -*- coding: iso-8859-10 -*-
"""Views for app knx"""
import csv
import os

def create_xml():
    csv_file = 'ga.csv'
    xml_file = settings.XML_TARGET_URL

    csv_data = csv.reader(open(f"{ settings.MEDIA_ROOT }{ csv_file }", encoding='latin-1'))
    data = [line for line in csv_data]
    xml_data = open(xml_file, 'w')
    xml_data.write(
    '''<?xml version="1.0"?>
    '''
    )
    # there must be only one top-level tag
    xml_data.write(
"""
<SnomIPPhoneMenu document_id="control">
    <Title>KNX Snom</Title>"""
    )

    tag1 = ''
    tag2 = ''

    for row in data:
        if '/-/-' in row[1]:
            if tag2 == 'open':
                xml_data.write(
        """
        </Menu>"""
                )
                tag2 = ''

            if tag1 == 'open':
                xml_data.write(
    """
    </Menu>"""
                )
                tag1 = ''   

            xml_data.write(
    f"""
    <Menu Name='{ row[0] }'>
    <Name>{ row[0] }</Name>"""
                )
            tag1 = 'open'
            continue

        elif '/-' in row[1]:
            if tag2 == 'open':
                xml_data.write(
        """
        </Menu>"""
                )
            tag2 = ''

            xml_data.write(
        f"""
        <Menu Name='{ row[0] }'>
        <Name>{ row[0] }</Name>"""
            )
            tag2 = 'open'
            continue

        elif 'DPST-1-' in row[5] and row[5] != 'DPST-1-11':
            xml_data.write(
            f"""
            <Menu Name='{ row[0] }'>
            <Name>{ row[0] }</Name>
                <MenuItem>
                <Name>on</Name>
                    <URL>{ settings.KNX_ROOT }{ row[1] }-an</URL>
                </MenuItem>
                <MenuItem>
                <Name>off</Name>
                    <URL>{ settings.KNX_ROOT }{ row[1] }-aus</URL>
                </MenuItem>
            </Menu>"""
            )
            continue
        elif 'DPST-3-' in row[5]:
            xml_data.write(
            f"""
            <Menu Name='{ row[0] }'>
            <Name>{ row[0] }</Name>
                <MenuItem>
                <Name>plus</Name>
                    <URL>{ settings.KNX_ROOT }{ row[1] }-plus</URL>
                </MenuItem>
                <MenuItem>
                <Name>minus</Name>
                    <URL>{ settings.KNX_ROOT }{ row[1] }-minus</URL>
                </MenuItem>
            </Menu>"""
            )
            continue

        elif '-' not in row[1]:
            continue

        if tag1 == 'open':
                xml_data.write(
        """
        </Menu>"""
                )
                tag1 = ''

    if tag2 == 'open':
            xml_data.write(
        """
        </Menu>"""
            )
            tag2 = ''
    if tag1 == 'open':

        xml_data.write(
    """
    </Menu>"""
        )

    xml_data.write(
    """
</SnomIPPhoneMenu>"""
    )
    xml_data.close()

    return xml_data

def make_action_menu(data, menu_name, top_menu):
    xml_file=f"{xml_physical_root}/{top_menu.replace('/',SEPERATOR)}.xml"
    if os.path.exists(xml_file):
        os.remove(xml_file)
    else:
        print("The file does not exist")

    xml_data = open(xml_file, 'w', encoding=ENCODING)

    top_menu_split = top_menu.split("/")

    xml_data.write(f"""<SnomIPPhoneMenu>
    <Title>{menu_name}</Title>""")

    for row_action_menu in data:
        row_split = row_action_menu[1].split("/")
        if row_split[0] == top_menu_split[0] and row_split[1] == top_menu_split[1] and row_split[2] != '-': 
            action_split = row_action_menu[5].split("-")
            if action_split[0] == 'DPST' and action_split[1] == '1' and action_split[2] != '11':
                xml_data.write(f"""
        <MenuItem>
            <Name>{ row_action_menu[0] }</Name>
        </MenuItem>
        <MenuItem>
            <Name>AN</Name>
            <URL>{ settings_KNX_ROOT }{ row_action_menu[1] }-an</URL>
        </MenuItem>
        <MenuItem>
            <Name>AUS</Name>
            <URL>{ settings_KNX_ROOT}{ row_action_menu[1] }-aus</URL>
        </MenuItem>""")
    
    xml_data.write(f"""
</SnomIPPhoneMenu>""")

    xml_data.close()


def make_mid_menu(data, menu_name, top_menu):
    xml_file=f"{xml_physical_root}/{top_menu.replace('/',SEPERATOR)}.xml"
    if os.path.exists(xml_file):
        os.remove(xml_file)
    else:
        print("The file does not exist")

    xml_data = open(xml_file, 'w', encoding=ENCODING)

    top_menu_split = top_menu.split("/")

    xml_data.write(f"""<SnomIPPhoneMenu>
    <Title>{menu_name}</Title>""")

    for row_mid_menu in data:
        #print(row_mid_menu)
        row_split = row_mid_menu[1].split("/")
        if row_split[0] == top_menu_split[0] and row_split[1] != '-' and row_split[2] == '-':
            new_file_name = row_mid_menu[1].replace('/',SEPERATOR)

            xml_data.write(f"""
            <MenuItem>
                <Name>{ row_mid_menu[0] }</Name>
                <URL>{XML_HTTP_ROOT}/{new_file_name}.xml</URL>
            </MenuItem>""")
            make_action_menu(data, row_mid_menu[0], row_mid_menu[1])

    xml_data.write(f"""
    </SnomIPPhoneMenu>""")

    xml_data.close()


def create_xml_files(data, xml_file):

    if os.path.exists(xml_file):
        os.remove(xml_file)
    else:
        print("The file does not exist")

    xml_data = open(xml_file, 'w', encoding=ENCODING)
    xml_data.write(f"""<SnomIPPhoneMenu>
    <Title>Main</Title>""")

    for row in data:
        if '/-/-' in row[1]:
            new_file_name = row[1].replace('/',SEPERATOR)
            xml_data.write(f"""
        <MenuItem>
            <Name>{ row[0] }</Name>
            <URL>{XML_HTTP_ROOT}/{new_file_name}.xml</URL>
        </MenuItem>""")
            # next menu level
            make_mid_menu(data, row[0], row[1])
    xml_data.write(f"""
</SnomIPPhoneMenu>""")

    xml_data.close()


SEPERATOR='S'
settings_KNX_ROOT='http://127.0.0.1:1234/'
XML_HTTP_ROOT='http://192.168.188.201/xml'

# EDIT!!
#settings_KNX_ROOT=settings.KNX_ROOT

ENCODING='utf-8'
XML_TARGET_PATH='/usr/local/gateway/iot/knx/media'
XML_TARGET_FILE='knx.xml'
XML_TARGET_URL=f'{XML_TARGET_PATH}{XML_TARGET_FILE}'

# xml physical server root
xml_physical_root='/Users/oliver.wittig/Public/htdocs/xml'

def run_create_xml_files():
    global xml_physical_root

    csv_file = 'ga.csv'
    # csv file container
    #csv_data = csv.reader(open(f"{ settings.MEDIA_ROOT }{ csv_file }", encoding='latin-1'))
    csv_data = csv.reader(open(f"/Users/oliver.wittig/DECTMessagingDemonstrator/app/{ csv_file }", encoding='latin-1'))
    data = [line for line in csv_data]

    xml_file=f'{xml_physical_root}/knx_dect.xml'
    create_xml_files(data, xml_file)
    

if __name__ == "__main__":
    run_create_xml_files()
