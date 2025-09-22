from mongoengine import StringField, EnumField

from module.leech.beans.leech_file import LeechFile
from module.leech.constants.leech_file_tool import LeechFileTool


class LeechBunkrFile(LeechFile):
    # tool used to download the file
    tool = EnumField(LeechFileTool, required=True, default=LeechFileTool.BUNKR)
    actual_link = StringField()

