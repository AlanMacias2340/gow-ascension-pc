#import <Cocoa/Cocoa.h>

/* 1: this process shows in the Dock. 0: it does not. A direct objc_msgSend
 * from Python crashes, so the launcher calls this instead. */
void ascension_dock(int show)
{
    [NSApp setActivationPolicy: show ? NSApplicationActivationPolicyRegular
                                     : NSApplicationActivationPolicyAccessory];
}
