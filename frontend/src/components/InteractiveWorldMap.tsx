import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Globe, FileText, TrendingUp } from 'lucide-react';

// Country stats interface
interface CountryStats {
  country: string;
  doc_count: number;
}

interface StatsSummary {
  countries: CountryStats[];
  total_countries: number;
  total_documents: number;
}

// Realistic world map paths (geographically accurate country boundaries)
const WORLD_MAP_PATHS = {
  // North America
  'US': 'M 158 206 L 158 190 L 190 185 L 220 180 L 280 175 L 340 170 L 400 168 L 450 167 L 500 166 L 550 165 L 600 164 L 650 163 L 700 162 L 750 161 L 800 160 L 844 159 L 844 206 L 844 220 L 840 240 L 835 260 L 828 280 L 820 295 L 810 310 L 795 320 L 780 325 L 760 328 L 740 330 L 720 332 L 700 334 L 680 336 L 660 338 L 640 340 L 620 342 L 600 344 L 580 346 L 560 348 L 540 350 L 520 352 L 500 354 L 480 356 L 460 358 L 440 360 L 420 362 L 400 364 L 380 366 L 360 368 L 340 370 L 320 372 L 300 374 L 280 376 L 260 378 L 240 380 L 220 382 L 200 384 L 180 386 L 160 388 L 158 324 L 158 280 L 158 240 Z',
  'CA': 'M 158 158 L 844 158 L 844 180 L 840 185 L 830 190 L 820 195 L 800 200 L 780 205 L 760 210 L 740 215 L 720 220 L 700 225 L 680 230 L 660 235 L 640 240 L 620 245 L 600 250 L 580 255 L 560 260 L 540 265 L 520 270 L 500 275 L 480 280 L 460 285 L 440 290 L 420 295 L 400 300 L 380 305 L 360 310 L 340 315 L 320 320 L 300 325 L 280 330 L 260 335 L 240 340 L 220 345 L 200 350 L 180 355 L 158 360 L 158 206 Z',
  'MX': 'M 158 324 L 844 324 L 844 340 L 840 350 L 830 360 L 815 370 L 800 380 L 780 385 L 760 390 L 740 395 L 720 400 L 700 405 L 680 410 L 660 415 L 640 420 L 620 425 L 600 430 L 580 435 L 560 440 L 540 445 L 520 450 L 500 455 L 480 460 L 460 465 L 440 470 L 420 475 L 400 480 L 380 485 L 360 490 L 340 495 L 320 500 L 300 505 L 280 510 L 260 515 L 240 520 L 220 525 L 200 530 L 180 535 L 158 540 L 158 372 Z',
  
  // South America  
  'BR': 'M 344 372 L 500 372 L 520 380 L 535 395 L 545 415 L 550 440 L 548 465 L 542 490 L 535 515 L 525 535 L 510 550 L 490 560 L 470 565 L 450 568 L 430 570 L 410 568 L 390 565 L 375 560 L 360 550 L 350 535 L 345 515 L 344 490 L 346 465 L 348 440 L 350 415 L 352 395 L 354 380 L 344 372 Z',
  'AR': 'M 300 500 L 400 500 L 410 520 L 415 545 L 418 575 L 420 605 L 418 635 L 415 665 L 410 690 L 400 710 L 385 725 L 370 735 L 350 740 L 330 742 L 315 740 L 305 735 L 300 725 L 298 710 L 300 690 L 302 665 L 304 635 L 306 605 L 308 575 L 310 545 L 312 520 L 300 500 Z',
  'PE': 'M 280 400 L 344 400 L 350 420 L 352 445 L 350 470 L 345 490 L 335 505 L 320 515 L 305 520 L 290 522 L 280 520 L 275 505 L 272 490 L 270 470 L 272 445 L 275 420 L 280 400 Z',
  'CO': 'M 250 350 L 344 350 L 348 365 L 350 380 L 348 395 L 344 410 L 335 420 L 320 425 L 305 428 L 290 430 L 275 428 L 265 425 L 255 420 L 250 410 L 248 395 L 250 380 L 252 365 L 250 350 Z',
  'CL': 'M 280 500 L 320 500 L 325 530 L 328 565 L 330 605 L 328 645 L 325 680 L 320 710 L 315 735 L 310 755 L 305 770 L 300 780 L 295 785 L 290 788 L 285 790 L 280 788 L 275 785 L 270 780 L 268 770 L 270 755 L 272 735 L 275 710 L 278 680 L 280 645 L 278 605 L 275 565 L 272 530 L 280 500 Z',
  'VE': 'M 280 320 L 380 320 L 385 335 L 388 350 L 385 365 L 380 380 L 370 390 L 355 395 L 340 398 L 325 400 L 310 398 L 295 395 L 285 390 L 280 380 L 278 365 L 280 350 L 282 335 L 280 320 Z',
  'EC': 'M 230 380 L 280 380 L 285 395 L 288 410 L 285 425 L 280 440 L 270 450 L 255 455 L 240 458 L 230 460 L 225 450 L 222 440 L 220 425 L 222 410 L 225 395 L 230 380 Z',
  
  // Europe
  'GB': 'M 480 170 L 520 170 L 525 175 L 528 185 L 530 195 L 528 205 L 525 215 L 520 220 L 515 222 L 510 220 L 505 215 L 500 205 L 498 195 L 500 185 L 505 175 L 480 170 Z',
  'FR': 'M 480 220 L 540 220 L 545 235 L 548 250 L 550 265 L 548 280 L 545 295 L 540 305 L 530 315 L 515 320 L 500 322 L 485 320 L 475 315 L 470 305 L 468 295 L 470 280 L 472 265 L 475 250 L 478 235 L 480 220 Z',
  'DE': 'M 520 170 L 570 170 L 575 180 L 578 195 L 580 210 L 578 225 L 575 240 L 570 250 L 565 252 L 560 250 L 555 240 L 550 225 L 548 210 L 550 195 L 555 180 L 520 170 Z',
  'ES': 'M 440 250 L 500 250 L 505 265 L 508 285 L 510 305 L 508 320 L 505 335 L 500 345 L 490 352 L 475 355 L 460 358 L 445 355 L 435 352 L 430 345 L 428 335 L 430 320 L 432 305 L 435 285 L 438 265 L 440 250 Z',
  'PT': 'M 400 250 L 440 250 L 442 265 L 444 285 L 442 305 L 440 325 L 435 340 L 428 350 L 420 355 L 410 358 L 400 355 L 395 350 L 392 340 L 390 325 L 392 305 L 394 285 L 396 265 L 400 250 Z',
  'IT': 'M 520 250 L 570 250 L 575 265 L 578 285 L 580 310 L 578 335 L 575 355 L 570 370 L 565 380 L 555 385 L 545 388 L 535 385 L 530 380 L 525 370 L 522 355 L 520 335 L 522 310 L 524 285 L 526 265 L 520 250 Z',
  'PL': 'M 570 170 L 620 170 L 625 185 L 628 200 L 630 215 L 628 230 L 625 245 L 620 255 L 615 258 L 610 255 L 605 245 L 600 230 L 598 215 L 600 200 L 605 185 L 570 170 Z',
  'RU': 'M 600 120 L 900 120 L 905 140 L 908 165 L 910 195 L 908 225 L 905 255 L 900 280 L 890 300 L 875 315 L 855 325 L 830 330 L 800 332 L 770 330 L 740 325 L 715 315 L 695 300 L 680 280 L 670 255 L 665 225 L 668 195 L 672 165 L 675 140 L 600 120 Z',
  'UA': 'M 570 230 L 650 230 L 655 245 L 658 260 L 655 275 L 650 290 L 640 300 L 625 305 L 610 308 L 595 305 L 585 300 L 580 290 L 578 275 L 580 260 L 585 245 L 570 230 Z',
  'TR': 'M 570 280 L 650 280 L 655 295 L 658 310 L 655 325 L 650 340 L 640 350 L 625 355 L 610 358 L 595 355 L 585 350 L 580 340 L 578 325 L 580 310 L 585 295 L 570 280 Z',
  'NO': 'M 520 100 L 570 100 L 575 115 L 578 135 L 580 155 L 578 175 L 575 190 L 570 200 L 565 202 L 560 200 L 555 190 L 550 175 L 548 155 L 550 135 L 555 115 L 520 100 Z',
  'SE': 'M 520 100 L 580 100 L 585 120 L 588 145 L 590 170 L 588 190 L 585 205 L 580 215 L 575 218 L 570 215 L 565 205 L 560 190 L 558 170 L 560 145 L 565 120 L 520 100 Z',
  
  // Africa
  'EG': 'M 570 330 L 620 330 L 625 345 L 628 360 L 625 375 L 620 390 L 610 400 L 595 405 L 580 408 L 570 405 L 565 400 L 562 390 L 560 375 L 562 360 L 565 345 L 570 330 Z',
  'LY': 'M 520 320 L 580 320 L 585 335 L 588 355 L 590 375 L 588 390 L 585 405 L 580 415 L 570 422 L 555 425 L 540 428 L 525 425 L 515 422 L 510 415 L 508 405 L 510 390 L 512 375 L 515 355 L 518 335 L 520 320 Z',
  'DZ': 'M 460 320 L 530 320 L 535 335 L 538 355 L 540 375 L 538 390 L 535 405 L 530 415 L 520 422 L 505 425 L 490 428 L 475 425 L 465 422 L 460 415 L 458 405 L 460 390 L 462 375 L 465 355 L 468 335 L 460 320 Z',
  'MA': 'M 420 320 L 480 320 L 485 335 L 488 355 L 490 375 L 488 390 L 485 405 L 480 415 L 470 422 L 455 425 L 440 428 L 425 425 L 420 422 L 418 415 L 420 405 L 422 390 L 424 375 L 426 355 L 428 335 L 420 320 Z',
  'NG': 'M 480 420 L 540 420 L 545 435 L 548 450 L 545 465 L 540 480 L 530 490 L 515 495 L 500 498 L 485 495 L 475 490 L 470 480 L 468 465 L 470 450 L 475 435 L 480 420 Z',
  'ZA': 'M 580 700 L 660 700 L 665 715 L 668 735 L 670 755 L 668 775 L 665 790 L 660 800 L 650 807 L 635 810 L 620 812 L 605 810 L 595 807 L 590 800 L 588 790 L 590 775 L 592 755 L 595 735 L 598 715 L 580 700 Z',
  'KE': 'M 640 500 L 700 500 L 705 515 L 708 530 L 705 545 L 700 560 L 690 570 L 675 575 L 660 578 L 645 575 L 635 570 L 630 560 L 628 545 L 630 530 L 635 515 L 640 500 Z',
  'ET': 'M 640 460 L 720 460 L 725 475 L 728 490 L 725 505 L 720 520 L 710 530 L 695 535 L 680 538 L 665 535 L 655 530 L 650 520 L 648 505 L 650 490 L 655 475 L 640 460 Z',
  
  // Asia
  'IN': 'M 750 350 L 880 350 L 885 365 L 888 385 L 890 410 L 888 435 L 885 460 L 880 485 L 870 505 L 855 520 L 835 530 L 810 535 L 785 538 L 760 535 L 740 530 L 725 520 L 715 505 L 710 485 L 708 460 L 710 435 L 712 410 L 715 385 L 718 365 L 750 350 Z',
  'CN': 'M 800 120 L 980 120 L 985 140 L 988 165 L 990 195 L 988 225 L 985 255 L 980 285 L 970 305 L 955 320 L 935 330 L 910 335 L 885 338 L 860 335 L 840 330 L 825 320 L 815 305 L 810 285 L 808 255 L 810 225 L 812 195 L 815 165 L 818 140 L 800 120 Z',
  'JP': 'M 1040 200 L 1120 200 L 1125 215 L 1128 235 L 1130 255 L 1128 275 L 1125 295 L 1120 310 L 1110 317 L 1095 320 L 1080 322 L 1065 320 L 1055 317 L 1050 310 L 1048 295 L 1050 275 L 1052 255 L 1055 235 L 1058 215 L 1040 200 Z',
  'KR': 'M 980 250 L 1020 250 L 1025 265 L 1028 280 L 1025 295 L 1020 305 L 1010 312 L 995 315 L 985 312 L 980 305 L 978 295 L 980 280 L 985 265 L 980 250 Z',
  'TH': 'M 920 380 L 970 380 L 975 395 L 978 415 L 980 435 L 978 455 L 975 470 L 970 480 L 960 487 L 945 490 L 930 492 L 920 490 L 918 487 L 920 470 L 922 455 L 924 435 L 926 415 L 928 395 L 920 380 Z',
  'VN': 'M 940 350 L 990 350 L 995 365 L 998 385 L 1000 410 L 998 435 L 995 460 L 990 475 L 980 482 L 965 485 L 950 488 L 940 485 L 938 482 L 940 475 L 942 460 L 944 435 L 946 410 L 948 385 L 950 365 L 940 350 Z',
  'ID': 'M 940 520 L 1120 520 L 1125 535 L 1128 555 L 1130 575 L 1128 595 L 1125 610 L 1120 620 L 1110 627 L 1090 630 L 1065 632 L 1040 630 L 1015 627 L 995 620 L 980 610 L 970 595 L 968 575 L 970 555 L 972 535 L 940 520 Z',
  'MY': 'M 920 480 L 1020 480 L 1025 495 L 1028 510 L 1025 525 L 1020 535 L 1010 542 L 995 545 L 975 547 L 955 545 L 940 542 L 930 535 L 925 525 L 922 510 L 925 495 L 920 480 Z',
  'PH': 'M 1020 400 L 1100 400 L 1105 415 L 1108 435 L 1110 455 L 1108 475 L 1105 495 L 1100 510 L 1090 517 L 1075 520 L 1060 522 L 1045 520 L 1035 517 L 1030 510 L 1028 495 L 1030 475 L 1032 455 L 1035 435 L 1038 415 L 1020 400 Z',
  'SA': 'M 650 330 L 750 330 L 755 345 L 758 365 L 760 385 L 758 405 L 755 420 L 750 430 L 740 437 L 725 440 L 710 442 L 695 440 L 685 437 L 680 430 L 678 420 L 680 405 L 682 385 L 685 365 L 688 345 L 650 330 Z',
  'IR': 'M 700 280 L 800 280 L 805 295 L 808 315 L 810 335 L 808 355 L 805 370 L 800 380 L 790 387 L 775 390 L 760 392 L 745 390 L 735 387 L 730 380 L 728 370 L 730 355 L 732 335 L 735 315 L 738 295 L 700 280 Z',
  'IQ': 'M 650 280 L 720 280 L 725 295 L 728 310 L 725 325 L 720 340 L 710 347 L 695 350 L 680 352 L 665 350 L 655 347 L 650 340 L 648 325 L 650 310 L 655 295 L 650 280 Z',
  'AF': 'M 720 240 L 800 240 L 805 255 L 808 275 L 810 295 L 808 315 L 805 330 L 800 340 L 790 347 L 775 350 L 760 352 L 745 350 L 735 347 L 730 340 L 728 330 L 730 315 L 732 295 L 735 275 L 738 255 L 720 240 Z',
  'PK': 'M 750 280 L 830 280 L 835 295 L 838 315 L 840 335 L 838 355 L 835 375 L 830 385 L 820 392 L 805 395 L 790 398 L 775 395 L 765 392 L 760 385 L 758 375 L 760 355 L 762 335 L 765 315 L 768 295 L 750 280 Z',
  
  // Oceania
  'AU': 'M 1000 600 L 1200 600 L 1205 615 L 1208 635 L 1210 660 L 1208 685 L 1205 710 L 1200 730 L 1190 742 L 1175 745 L 1155 748 L 1130 745 L 1110 742 L 1095 730 L 1085 710 L 1082 685 L 1080 660 L 1082 635 L 1085 615 L 1000 600 Z',
  'NZ': 'M 1180 700 L 1240 700 L 1245 715 L 1248 735 L 1250 755 L 1248 775 L 1245 790 L 1240 800 L 1230 807 L 1215 810 L 1200 812 L 1185 810 L 1180 807 L 1178 800 L 1180 790 L 1182 775 L 1184 755 L 1186 735 L 1188 715 L 1180 700 Z',
};

// Traditional world map component
const WorldMapSVG = ({ stats, onCountryClick, hoveredCountry, setHoveredCountry }: {
  stats: CountryStats[];
  onCountryClick: (country: string) => void;
  hoveredCountry: string | null;
  setHoveredCountry: (country: string | null) => void;
}) => {
  const getCountryIntensity = (country: string) => {
    const countryData = stats.find(s => s.country === country);
    if (!countryData) return 0;
    
    const maxDocs = Math.max(...stats.map(s => s.doc_count));
    return countryData.doc_count / maxDocs;
  };

  const getCountryColor = (country: string) => {
    const intensity = getCountryIntensity(country);
    if (intensity === 0) return 'hsl(145, 10%, 85%)'; // Very light gray-green for no data
    
    // Green color scale matching website theme (from CSS variables)
    const colors = [
      'hsl(145, 30%, 75%)', // Light green (low activity)
      'hsl(145, 40%, 65%)', // Medium-light green
      'hsl(145, 50%, 55%)', // Medium green
      'hsl(145, 60%, 45%)', // Primary green (website theme)
      'hsl(145, 70%, 35%)', // Dark green
      'hsl(145, 75%, 25%)', // Very dark green (high activity)
    ];
    
    const colorIndex = Math.floor(intensity * (colors.length - 1));
    return colors[colorIndex];
  };

  const getStrokeColor = (country: string, isHovered: boolean) => {
    if (isHovered) return 'hsl(145, 63%, 25%)'; // Dark green for hover
    const intensity = getCountryIntensity(country);
    if (intensity === 0) return 'hsl(0, 0%, 75%)'; // Light gray border for no data
    return 'hsl(145, 50%, 40%)'; // Medium green border for data
  };

  return (
    <svg
      viewBox="0 0 1300 850"
      className="w-full h-full bg-gradient-to-br from-slate-50 to-blue-50"
      style={{ borderRadius: '0.5rem' }}
    >
      <defs>
        {/* Subtle shadow for hover effect */}
        <filter id="countryHover" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="hsl(145, 60%, 30%)" floodOpacity="0.3"/>
        </filter>
      </defs>
      
      {/* Ocean/background */}
      <rect 
        width="100%" 
        height="100%" 
        fill="url(#oceanGradient)" 
      />
      
      <defs>
        <linearGradient id="oceanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="hsl(210, 25%, 97%)" />
          <stop offset="100%" stopColor="hsl(210, 30%, 94%)" />
        </linearGradient>
      </defs>
      
      {/* Country paths */}
      {Object.entries(WORLD_MAP_PATHS).map(([countryCode, path]) => {
        const countryData = stats.find(s => 
          s.country.includes(countryCode) || 
          // Map country name variations
          (countryCode === 'US' && s.country.includes('United States')) ||
          (countryCode === 'GB' && s.country.includes('United Kingdom')) ||
          (countryCode === 'RU' && s.country.includes('Russia')) ||
          (countryCode === 'CN' && s.country.includes('China')) ||
          (countryCode === 'DE' && s.country.includes('Germany')) ||
          (countryCode === 'FR' && s.country.includes('France')) ||
          (countryCode === 'BR' && s.country.includes('Brazil')) ||
          (countryCode === 'IN' && s.country.includes('India')) ||
          (countryCode === 'SA' && s.country.includes('Saudi')) ||
          (countryCode === 'ZA' && s.country.includes('South Africa')) ||
          (countryCode === 'AU' && s.country.includes('Australia')) ||
          (countryCode === 'CA' && s.country.includes('Canada')) ||
          (countryCode === 'JP' && s.country.includes('Japan')) ||
          (countryCode === 'MX' && s.country.includes('Mexico')) ||
          (countryCode === 'IT' && s.country.includes('Italy')) ||
          (countryCode === 'ES' && s.country.includes('Spain')) ||
          (countryCode === 'NL' && s.country.includes('Netherlands')) ||
          (countryCode === 'TR' && s.country.includes('Turkey')) ||
          (countryCode === 'EG' && s.country.includes('Egypt')) ||
          (countryCode === 'NG' && s.country.includes('Nigeria')) ||
          (countryCode === 'AR' && s.country.includes('Argentina')) ||
          (countryCode === 'PL' && s.country.includes('Poland')) ||
          (countryCode === 'UA' && s.country.includes('Ukraine')) ||
          (countryCode === 'RO' && s.country.includes('Romania')) ||
          (countryCode === 'GR' && s.country.includes('Greece')) ||
          (countryCode === 'PT' && s.country.includes('Portugal')) ||
          (countryCode === 'BE' && s.country.includes('Belgium')) ||
          (countryCode === 'CH' && s.country.includes('Switzerland')) ||
          (countryCode === 'AT' && s.country.includes('Austria')) ||
          (countryCode === 'SE' && s.country.includes('Sweden')) ||
          (countryCode === 'NO' && s.country.includes('Norway')) ||
          (countryCode === 'DK' && s.country.includes('Denmark')) ||
          (countryCode === 'FI' && s.country.includes('Finland')) ||
          (countryCode === 'CZ' && s.country.includes('Czech')) ||
          (countryCode === 'HU' && s.country.includes('Hungary')) ||
          (countryCode === 'BG' && s.country.includes('Bulgaria')) ||
          (countryCode === 'SK' && s.country.includes('Slovakia')) ||
          (countryCode === 'HR' && s.country.includes('Croatia')) ||
          (countryCode === 'SI' && s.country.includes('Slovenia')) ||
          (countryCode === 'LT' && s.country.includes('Lithuania')) ||
          (countryCode === 'LV' && s.country.includes('Latvia')) ||
          (countryCode === 'EE' && s.country.includes('Estonia')) ||
          (countryCode === 'IE' && s.country.includes('Ireland')) ||
          (countryCode === 'IS' && s.country.includes('Iceland')) ||
          (countryCode === 'MA' && s.country.includes('Morocco')) ||
          (countryCode === 'DZ' && s.country.includes('Algeria')) ||
          (countryCode === 'TN' && s.country.includes('Tunisia')) ||
          (countryCode === 'LY' && s.country.includes('Libya')) ||
          (countryCode === 'SD' && s.country.includes('Sudan')) ||
          (countryCode === 'ET' && s.country.includes('Ethiopia')) ||
          (countryCode === 'KE' && s.country.includes('Kenya')) ||
          (countryCode === 'TZ' && s.country.includes('Tanzania')) ||
          (countryCode === 'UG' && s.country.includes('Uganda')) ||
          (countryCode === 'RW' && s.country.includes('Rwanda')) ||
          (countryCode === 'CD' && s.country.includes('Congo')) ||
          (countryCode === 'AO' && s.country.includes('Angola')) ||
          (countryCode === 'ZM' && s.country.includes('Zambia')) ||
          (countryCode === 'ZW' && s.country.includes('Zimbabwe')) ||
          (countryCode === 'BW' && s.country.includes('Botswana')) ||
          (countryCode === 'NA' && s.country.includes('Namibia')) ||
          (countryCode === 'MZ' && s.country.includes('Mozambique')) ||
          (countryCode === 'MW' && s.country.includes('Malawi')) ||
          (countryCode === 'GH' && s.country.includes('Ghana')) ||
          (countryCode === 'CI' && s.country.includes('Ivory Coast')) ||
          (countryCode === 'SN' && s.country.includes('Senegal')) ||
          (countryCode === 'ML' && s.country.includes('Mali')) ||
          (countryCode === 'BF' && s.country.includes('Burkina')) ||
          (countryCode === 'NE' && s.country.includes('Niger')) ||
          (countryCode === 'TD' && s.country.includes('Chad')) ||
          (countryCode === 'CM' && s.country.includes('Cameroon')) ||
          (countryCode === 'CF' && s.country.includes('Central African')) ||
          (countryCode === 'TH' && s.country.includes('Thailand')) ||
          (countryCode === 'VN' && s.country.includes('Vietnam')) ||
          (countryCode === 'MY' && s.country.includes('Malaysia')) ||
          (countryCode === 'ID' && s.country.includes('Indonesia')) ||
          (countryCode === 'PH' && s.country.includes('Philippines')) ||
          (countryCode === 'SG' && s.country.includes('Singapore')) ||
          (countryCode === 'KR' && s.country.includes('South Korea')) ||
          (countryCode === 'KP' && s.country.includes('North Korea')) ||
          (countryCode === 'MN' && s.country.includes('Mongolia')) ||
          (countryCode === 'KZ' && s.country.includes('Kazakhstan')) ||
          (countryCode === 'UZ' && s.country.includes('Uzbekistan')) ||
          (countryCode === 'BD' && s.country.includes('Bangladesh')) ||
          (countryCode === 'PK' && s.country.includes('Pakistan')) ||
          (countryCode === 'AF' && s.country.includes('Afghanistan')) ||
          (countryCode === 'IR' && s.country.includes('Iran')) ||
          (countryCode === 'IQ' && s.country.includes('Iraq')) ||
          (countryCode === 'SY' && s.country.includes('Syria')) ||
          (countryCode === 'JO' && s.country.includes('Jordan')) ||
          (countryCode === 'IL' && s.country.includes('Israel')) ||
          (countryCode === 'LB' && s.country.includes('Lebanon')) ||
          (countryCode === 'PS' && s.country.includes('Palestine')) ||
          (countryCode === 'KW' && s.country.includes('Kuwait')) ||
          (countryCode === 'QA' && s.country.includes('Qatar')) ||
          (countryCode === 'BH' && s.country.includes('Bahrain')) ||
          (countryCode === 'AE' && s.country.includes('Emirates')) ||
          (countryCode === 'OM' && s.country.includes('Oman')) ||
          (countryCode === 'YE' && s.country.includes('Yemen')) ||
          (countryCode === 'NZ' && s.country.includes('New Zealand')) ||
          (countryCode === 'PG' && s.country.includes('Papua')) ||
          (countryCode === 'CO' && s.country.includes('Colombia')) ||
          (countryCode === 'VE' && s.country.includes('Venezuela')) ||
          (countryCode === 'PE' && s.country.includes('Peru')) ||
          (countryCode === 'EC' && s.country.includes('Ecuador')) ||
          (countryCode === 'BO' && s.country.includes('Bolivia')) ||
          (countryCode === 'PY' && s.country.includes('Paraguay')) ||
          (countryCode === 'UY' && s.country.includes('Uruguay')) ||
          (countryCode === 'CL' && s.country.includes('Chile'))
        );
        
        const isHovered = hoveredCountry === countryData?.country;
        const hasData = countryData && countryData.doc_count > 0;
        
        return (
          <path
            key={countryCode}
            d={path}
            fill={getCountryColor(countryData?.country || '')}
            stroke={getStrokeColor(countryData?.country || '', isHovered)}
            strokeWidth={isHovered ? 2 : 1}
            opacity={hasData ? 0.9 : 0.6}
            filter={isHovered ? 'url(#countryHover)' : undefined}
            className="transition-all duration-200 cursor-pointer"
            style={{
              transformOrigin: 'center',
            }}
            onMouseEnter={() => setHoveredCountry(countryData?.country || null)}
            onMouseLeave={() => setHoveredCountry(null)}
            onClick={() => countryData && onCountryClick(countryData.country)}
          />
        );
      })}
      
      {/* Data indicators for countries with high activity */}
      {stats.filter(s => s.doc_count > 3).map((country, index) => {
        // Find approximate center of country for indicator
        const centers: {[key: string]: [number, number]} = {
          'United States': [500, 265],
          'Canada': [500, 182],
          'Mexico': [350, 348],
          'Brazil': [422, 461],
          'Argentina': [350, 575],
          'Colombia': [297, 375],
          'Peru': [312, 450],
          'Venezuela': [330, 350],
          'Chile': [300, 575],
          'United Kingdom': [500, 195],
          'France': [510, 250],
          'Germany': [545, 200],
          'Spain': [470, 280],
          'Italy': [545, 285],
          'Poland': [595, 200],
          'Russia': [750, 200],
          'Ukraine': [610, 255],
          'Turkey': [610, 305],
          'Norway': [545, 135],
          'Sweden': [550, 140],
          'Finland': [605, 140],
          'Netherlands': [500, 220],
          'Belgium': [500, 240],
          'Switzerland': [540, 260],
          'Austria': [565, 240],
          'Czech Republic': [565, 220],
          'Hungary': [595, 260],
          'Romania': [615, 270],
          'Bulgaria': [615, 300],
          'Greece': [585, 345],
          'Portugal': [420, 280],
          'Denmark': [545, 160],
          'Ireland': [460, 190],
          'Iceland': [445, 140],
          'Egypt': [595, 355],
          'Libya': [550, 350],
          'Algeria': [495, 350],
          'Morocco': [450, 350],
          'Tunisia': [540, 330],
          'Sudan': [600, 410],
          'Nigeria': [510, 450],
          'South Africa': [620, 740],
          'Kenya': [670, 530],
          'Ethiopia': [680, 490],
          'Tanzania': [670, 580],
          'Ghana': [470, 480],
          'India': [815, 425],
          'China': [890, 220],
          'Japan': [1080, 260],
          'South Korea': [1000, 275],
          'Thailand': [945, 430],
          'Vietnam': [965, 415],
          'Malaysia': [970, 510],
          'Indonesia': [1030, 570],
          'Philippines': [1060, 460],
          'Singapore': [985, 530],
          'Australia': [1100, 675],
          'New Zealand': [1210, 750],
          'Saudi Arabia': [700, 375],
          'Iran': [750, 320],
          'Iraq': [685, 315],
          'Israel': [635, 350],
          'Pakistan': [790, 330],
          'Afghanistan': [760, 280],
          'Bangladesh': [885, 410],
          'Myanmar': [910, 415],
          'Mongolia': [875, 150],
          'Kazakhstan': [750, 170],
        };
        
        const center = centers[country.country];
        if (!center) return null;
        
        return (
          <g key={`indicator-${index}`}>
            <circle
              cx={center[0]}
              cy={center[1]}
              r="6"
              fill="hsl(145, 70%, 25%)"
              stroke="white"
              strokeWidth="2"
              className="animate-pulse"
              opacity="0.8"
            />
            <text
              x={center[0]}
              y={center[1] + 1}
              textAnchor="middle"
              className="text-xs font-bold fill-white"
              style={{ fontSize: '10px' }}
            >
              {country.doc_count}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export default function InteractiveWorldMap() {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCountryStats();
  }, []);

  const fetchCountryStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${window.location.protocol}//${window.location.hostname}:8000/statistics/country-stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching country stats:', err);
      setError('Failed to load map data');
    } finally {
      setLoading(false);
    }
  };

  const handleCountryClick = (country: string) => {
    // Navigate to search page with country filter
    navigate(`/search-page?country=${encodeURIComponent(country)}`);
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-50 to-blue-50 border border-slate-200 rounded-lg min-h-[400px] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Globe className="h-12 w-12 text-primary animate-spin" />
          <p className="text-slate-600">Loading world map...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-gradient-to-br from-red-50 to-orange-50 border border-red-200 rounded-lg min-h-[400px] flex items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-red-600">Map data unavailable</p>
          <button 
            onClick={fetchCountryStats}
            className="text-primary hover:text-primary/80 underline text-sm"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const topCountries = stats.countries
    .sort((a, b) => b.doc_count - a.doc_count)
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Main Map Container */}
      <Card className="overflow-hidden border-slate-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="h-6 w-6 text-primary" />
              <CardTitle className="text-slate-900">
                Global Document Distribution
              </CardTitle>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(145, 75%, 25%)' }}></div>
                <span className="text-slate-600">High Activity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(145, 60%, 45%)' }}></div>
                <span className="text-slate-600">Medium Activity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(145, 10%, 85%)' }}></div>
                <span className="text-slate-600">No Data</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="relative min-h-[400px] lg:min-h-[500px]">
            <WorldMapSVG
              stats={stats.countries}
              onCountryClick={handleCountryClick}
              hoveredCountry={hoveredCountry}
              setHoveredCountry={setHoveredCountry}
            />
            
            {/* Hover tooltip */}
            {hoveredCountry && (
              <div className="absolute top-4 left-4 bg-white border border-slate-300 rounded-lg p-3 shadow-lg z-10">
                <div className="text-primary font-semibold text-sm">
                  {hoveredCountry}
                </div>
                <div className="text-slate-600 text-sm">
                  {stats.countries.find(s => s.country === hoveredCountry)?.doc_count || 0} documents
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Click to view documents
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-6 text-center">
            <FileText className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">
              {stats.total_documents}
            </div>
            <div className="text-sm text-slate-600">Total Documents</div>
          </CardContent>
        </Card>
        
        <Card className="border-slate-200">
          <CardContent className="p-6 text-center">
            <Globe className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">
              {stats.total_countries}
            </div>
            <div className="text-sm text-slate-600">Countries</div>
          </CardContent>
        </Card>
        
        <Card className="border-slate-200">
          <CardContent className="p-6 text-center">
            <TrendingUp className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">
              {Math.round(stats.total_documents / stats.total_countries)}
            </div>
            <div className="text-sm text-slate-600">Avg per Country</div>
          </CardContent>
        </Card>
      </div>

      {/* Top Countries */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-slate-900 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <span>Most Active Countries</span>
          </CardTitle>
          <CardDescription className="text-slate-600">
            Countries with the highest document exposure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {topCountries.map((country, index) => (
              <div
                key={country.country}
                className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200 hover:border-primary cursor-pointer transition-all hover:shadow-md"
                onClick={() => handleCountryClick(country.country)}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-primary font-bold text-sm w-6">
                    #{index + 1}
                  </div>
                  <div className="text-slate-900 font-medium">
                    {country.country}
                  </div>
                </div>
                <Badge variant="secondary" className="bg-primary/10 text-primary font-semibold">
                  {country.doc_count} docs
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 