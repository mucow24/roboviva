# UGCS Doesn't have newer python versions, so we roll-our-own enums, here:
def Enum(**enums):
  return type('Enum', (), enums)
