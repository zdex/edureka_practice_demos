#!/usr/bin/env python
# coding: utf-8

# In[3]:


import math as m
import datetime as d


# In[5]:


print(dir(m))


# In[6]:


print(dir(d))


# In[8]:


import random as r


# In[10]:


print(dir(r))


# In[11]:


print(r.random())


# In[14]:


print(r.randrange(1,5))


# In[19]:


import json
print(dir(json))
import os
print(dir(os))


# In[30]:


person = {
    "name" : "gaurav",
    "age" : "30"
}
print(os.getcwd())
print(json.dumps(person))
print(help(json))


# In[31]:


def myname(name):
    return "my name is: " + name


# In[32]:


myname("gaurav")


# In[ ]:




