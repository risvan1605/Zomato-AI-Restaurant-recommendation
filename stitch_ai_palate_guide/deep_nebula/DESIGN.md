---
name: Deep Nebula
colors:
  surface: '#11112a'
  surface-dim: '#11112a'
  surface-bright: '#373752'
  surface-container-lowest: '#0b0b24'
  surface-container-low: '#191932'
  surface-container: '#1d1d37'
  surface-container-high: '#272742'
  surface-container-highest: '#32324d'
  on-surface: '#e2dfff'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#e2dfff'
  inverse-on-surface: '#2e2e48'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#11112a'
  on-background: '#e2dfff'
  surface-variant: '#32324d'
typography:
  headline-xl:
    fontFamily: Outfit
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1200px
  gutter: 20px
---

## Brand & Style

The design system is engineered to evoke a sense of premium discovery and celestial sophistication. Aimed at discerning food enthusiasts seeking AI-curated experiences, the interface relies on **Glassmorphism** to create a sense of depth and atmospheric immersion. 

The aesthetic mimics the depth of a night sky, utilizing translucent layers, vibrant background blurs, and ethereal glows to guide the user's eye toward high-value recommendations. Every interaction should feel fluid and expansive, shifting the user from a standard utility app into a curated, high-end concierge experience.

## Colors

This design system utilizes a deep, multi-tonal dark mode palette to establish a "Deep Nebula" environment. 

- **Backgrounds:** Never use flat black. Use the primary three-step indigo-to-violet gradient for the main viewport. Surface containers use semi-transparent variants of the neutral hex with backdrop filtering.
- **Accents:** Indigo and Violet are used for primary actions and brand flourishes. These should often be applied as soft gradients rather than flat fills to maintain the celestial theme.
- **Status:** Warm Amber is reserved exclusively for ratings and "star" indicators to provide a high-contrast focal point against the cool-toned background. Emerald is used for availability and success confirmations.

## Typography

The typography system strikes a balance between expressive character and utilitarian clarity. 

**Outfit** is used for all headings to provide a modern, geometric, and stylish flair that feels high-end. Use tight letter-spacing on larger headlines to increase visual impact.

**Inter** is the workhorse for all functional text. It ensures that restaurant descriptions, addresses, and menu items remain perfectly legible against the complex glassmorphic backgrounds. Use the Medium (500) or Semi-Bold (600) weights for labels and metadata to ensure they "pop" against translucent surfaces.

## Layout & Spacing

The design system follows a fluid-first approach with a generous 8px spatial rhythm. 

- **Grid:** Use a 12-column grid for desktop and a 4-column grid for mobile. 
- **Margins:** Maintain a minimum 24px side margin on mobile to allow the background gradient to frame the content.
- **Vertical Rhythm:** Use the `lg` (40px) and `xl` (64px) spacing tokens between major sections to emphasize the "minimalist" and "premium" feel. Content should never feel cramped; whitespace is a critical component of the luxury narrative.

## Elevation & Depth

Depth is the defining characteristic of this design system. It is achieved through three primary methods:

1.  **Backdrop Blurs:** Every interactive surface (cards, modals, navigation bars) must use a `backdrop-filter: blur()` between 12px and 20px.
2.  **Inner Highlights:** Apply a 0.5px solid white stroke with 10-15% opacity to the top and left edges of glass elements to simulate a light source hitting the "edge" of the glass.
3.  **Tinted Shadows:** Instead of black shadows, use deep indigo or violet shadows (`#0f0c29` at 40% opacity) with a wide spread (20px-40px) to create an atmospheric glow rather than a harsh drop-shadow.

## Shapes

The shape language is consistently rounded to feel approachable and modern. 

- **Standard Elements:** Buttons and inputs use a base 8px (`0.5rem`) radius.
- **Containers:** Large glass cards and restaurant detail modals use a more pronounced 24px (`1.5rem`) radius to soften the layout and emphasize the "capsule" feel of the AI recommendations. 
- **Interactive Indicators:** Elements like notification dots or selection rings should remain perfectly circular.

## Components

### Glass Cards
The core container for restaurant listings. Cards should have a background of white at 5% opacity, a 1px border of white at 10% opacity, and a 20px backdrop blur. 

### Gradient Buttons
Primary actions use a linear gradient from Indigo (#6366f1) to Violet (#8b5cf6). On hover, apply a `box-shadow` of the same colors with a 15px blur to create a "neon glow" effect. Text inside buttons should be 'Inter' Semi-Bold.

### Input Fields
Inputs are styled as "dark glass"—using the background color at a higher opacity (20%) with a subtle inner glow. On focus, the border transitions from faint white to a solid Indigo stroke with a 4px outer glow.

### Badges & Chips
Pill-shaped containers for cuisine types or price points. Use high-saturation background colors at 15% opacity with matching 100% opacity text. Add a very subtle outer glow in the same hue to make them appear self-illuminated.

### AI Suggestion Overlays
When the AI is "thinking" or presenting a top recommendation, use an animated border-gradient that cycles through the brand colors, paired with a more intense backdrop blur (30px) to isolate the suggestion from the background noise.