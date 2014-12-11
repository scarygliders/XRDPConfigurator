//# Copyright (c) 2014 Kevin Cave
//#
//# Licensed under the Apache License, Version 2.0 (the "License");
//# you may not use this file except in compliance with the License.
//# You may obtain a copy of the License at
//#
//# http://www.apache.org/licenses/LICENSE-2.0
//#
//# Unless required by applicable law or agreed to in writing, software
//# distributed under the License is distributed on an "AS IS" BASIS,
//# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//# See the License for the specific language governing permissions and
//# limitations under the License.
//#
//# -------------------------------------------------------------------------

// libxrdpconfigurator - Helper shared library for XRDPConfigurator, for generating keymaps.
// Uses a similar method to the xrdp project's xrdp-genkeymap to access Xlib in order to retrieve key codes.
// Most of the heavy lifting is done in Python, which then calls this helper lib, which then returns a key code
// back to the python application.
//
// The xrdp project can be found at https://github.com/neutrinolabs/xrdp

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <locale.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

char* getlookupstring(Display *dsplay, int keycode, int state);


char* getlookupstring(Display *dsplay, int keycode, int state)
{
    XKeyPressedEvent kpe;
    KeySym ksym; // an Xlib KeySym struct
    int count = 0; // size of the returned string in bytes.
    int code; // the returned unicode
    char text[256];
    wchar_t wtext[256];
    char *msgOut;

    memset(&kpe, 0, sizeof(kpe));
    kpe.type = KeyPress;
    kpe.serial = 16;
    kpe.send_event = True;
    kpe.display = dsplay;
    kpe.same_screen = True;
    kpe.keycode = keycode;
    kpe.state = state;
    count = XLookupString(&kpe, text, 255, &ksym, NULL);
    text[count] = 0;
    code = 0;
    if (mbstowcs(wtext, text, 255) == 1)
    {
        code = wtext[0];
    }
    asprintf(&msgOut, "Key%d=%d:%d", keycode, (int) ksym, code);
    char *msg_out = strdup(msgOut);
    return msg_out; // return the result back to the application.
}

void freeme(char *ptr)
{
  free(ptr);
}