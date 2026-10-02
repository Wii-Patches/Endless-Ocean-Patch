/* Classic Controller support for Endless Ocean (the first game).
 *
 * The game only knows the Wii Remote: a pointer to steer, B to swim, A to
 * interact.  Blue World, the sequel, plays with a Classic Controller by moving a
 * cursor with the left stick and steering with the right one, so the same layout
 * is used here, with the pointer standing in for both: it sits where the sticks
 * push it (a stick fully to one side puts the pointer on that edge of the screen,
 * which is how this game turns), and centres when they are released.
 *
 * A GameCube pad reaches the game as a Classic Controller (the GameCube feature
 * queues Classic Controller samples), so this one translation serves both.
 *
 * Two hooks in KPADiRead's per-sample loop:
 *   cc_buttons  Classic Controller buttons -> the Wii Remote buttons the game reads
 *   cc_pointer  sticks -> pointer position, after the (empty) IR routine has run
 */
typedef unsigned int u32;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned char u8;

/* Classic Controller buttons as WPAD reports them */
#define CL_UP    0x0001
#define CL_LEFT  0x0002
#define CL_ZR    0x0004
#define CL_X     0x0008
#define CL_A     0x0010
#define CL_Y     0x0020
#define CL_B     0x0040
#define CL_ZL    0x0080
#define CL_HOME  0x0800
#define CL_R     0x0200
#define CL_PLUS  0x0400
#define CL_MINUS 0x1000
#define CL_L     0x2000
#define CL_DOWN  0x4000
#define CL_RIGHT 0x8000

/* Wii Remote buttons */
#define WM_LEFT  0x0001
#define WM_RIGHT 0x0002
#define WM_DOWN  0x0004
#define WM_UP    0x0008
#define WM_PLUS  0x0010
#define WM_2     0x0100
#define WM_1     0x0200
#define WM_B     0x0400
#define WM_A     0x0800
#define WM_MINUS 0x1000
#define WM_HOME  0x8000

#if defined(HOOK_BUTTONS)
/* core = the sample's Wii Remote buttons, ext = its extension type, cc = the
 * Classic Controller buttons (0xFFFF when the sample carries none) */
u32 cc_buttons(u32 core, u32 ext, u32 cc)
{
    u32 w = 0;

    if (ext != 2 || cc == 0xFFFF)
        return core;
    if (cc & (CL_A | CL_R))     w |= WM_A;       /* check / use */
    if (cc & (CL_B | CL_L))     w |= WM_B;       /* swim / cancel */
    if (cc & CL_X)              w |= WM_1;       /* map */
    if (cc & (CL_Y | CL_ZR))    w |= WM_PLUS;    /* zoom */
    if (cc & (CL_PLUS | CL_ZL)) w |= WM_MINUS;   /* autoswim / zoom out */
    if (cc & CL_MINUS)          w |= WM_2;       /* change view */
    if (cc & CL_HOME)           w |= WM_HOME;
    if (cc & CL_UP)             w |= WM_UP;      /* tool menu */
    if (cc & CL_DOWN)           w |= WM_DOWN;
    if (cc & CL_LEFT)           w |= WM_LEFT;
    if (cc & CL_RIGHT)          w |= WM_RIGHT;
    return core | w;
}
#endif

#if defined(HOOK_POINTER)
/* float constants built through the stack: a literal pool would land outside
 * the blob, which is copied to a new address */
static inline float bits(u32 b)
{
    volatile u32 t = b;
    return *(volatile float *)&t;
}

static inline float clamp1(float v)
{
    float hi = bits(0x3F800000u), lo = bits(0xBF800000u);

    if (v > hi)
        return hi;
    if (v < lo)
        return lo;
    return v;
}

/* k = the channel's KPAD struct, s = the sample.  KPAD has already turned the
 * Classic Controller sticks into -1..1 floats with its dead zone: left stick at
 * +0x6C/+0x70, right stick at +0x74/+0x78 (y up).  The pointer is y down. */
void cc_pointer(u8 *k, u8 *s)
{
    float lx, ly, rx, ry;

    if (s[0x28] != 2 || s[0x29] != 0)
        return;
    lx = *(float *)(k + 0x6C);
    ly = *(float *)(k + 0x70);
    rx = *(float *)(k + 0x74);
    ry = *(float *)(k + 0x78);
    *(float *)(k + 0x20) = clamp1(lx + rx);
    *(float *)(k + 0x24) = clamp1(-(ly + ry));
    k[0x5E] = 2;                    /* pointer valid */
}
#endif
