
import type { Product } from './types';

export const PRODUCTS: Product[] = [
  {
    id: 'rs-01',
    name: 'River Sand',
    description: 'Fine grain sand, ideal for plastering and brickwork. Washed and screened.',
    price: 300,
    unit: 'ton',
    category: 'Sand',
    imageUrl: '/images/river_sand.jpg', // River Sand (Image 10)
  },
  {
    id: 'ps-01',
    name: 'Pit Sand',
    description: 'Coarse grain sand, used for backfill, bedding pipes and under paving.',
    price: 250,
    unit: 'ton',
    category: 'Sand',
    imageUrl: '/images/pit_sand.jpg', // Pit Sand (Image 9)
  },
   {
    id: 'pls-01',
    name: 'Plaster Sand',
    description: 'A very fine sand that is used for plastering finishing, giving a smooth finish.',
    price: 320,
    unit: 'ton',
    category: 'Sand',
    imageUrl: '/images/plastering_sand.jpg', // Plaster Sand (Image 8)
  },
  {
    id: 'cs-19',
    name: '19mm Concrete Stones',
    description: 'Standard 19mm crushed stone for strong concrete mixes in foundations and slabs.',
    price: 400,
    unit: 'ton',
    category: 'Stones',
    imageUrl: '/images/19mm_Concrete_Stones.jpg', // 19mm Concrete Stones (Image 5)
  },
    {
    id: 'gr-13',
    name: '13mm Gravel Stones',
    description: 'Smaller 13mm stone, ideal for pathways, drainage solutions and decorative purposes.',
    price: 420,
    unit: 'ton',
    category: 'Gravel',
    imageUrl: '/images/13mm_Gravel_Stones.jpg', // 13mm Gravel Stones (Image 6)
  },
  {
    id: 'gr-19',
    name: '19mm Driveway Gravel',
    description: 'Durable 19mm gravel for driveways, roads, and landscaping projects.',
    price: 380,
    unit: 'ton',
    category: 'Gravel',
    imageUrl: '/images/19mm_Driveway_Gravel.jpg', // 19mm Driveway Gravel (Image 7)
  },
  {
    id: 'cd-01',
    name: 'Crusher Dust',
    description: 'Fine quarry dust, excellent for final layers in paving and as a binding agent.',
    price: 220,
    unit: 'ton',
    category: 'Base Materials',
    imageUrl: '/images/Crusher_Dust.jpg', // Crusher Dust (Image 3)
  },
  {
    id: 'cr-19',
    name: '19mm Crusher Run',
    description: 'A mix of 19mm crushed stone and dust for a solid, compactable base under paving and roads.',
    price: 350,
    unit: 'ton',
    category: 'Base Materials',
    imageUrl: '/images/19mm_Crusher_Run.jpg', // 19mm Crusher Run (Image 4)
  },
  {
    id: 'bf-01',
    name: 'Backfill Material',
    description: 'Unprocessed material for filling large voids and trenches, good for foundations.',
    price: 180,
    unit: 'ton',
    category: 'Filling Materials',
    imageUrl: '/images/Backfill_Material.jpg', // Backfill Material (Image 1)
  },
  {
    id: 'g5-01',
    name: 'G5 Filling Material',
    description: 'Graded material that meets G5 specifications for road layer works and foundations.',
    price: 280,
    unit: 'ton',
    category: 'Filling Materials',
    imageUrl: '/images/G5_Filling_Material.jpg', // G5 Filling Material (Image 2)
  },
];

export const CATEGORIES = [
  'All',
  ...Array.from(new Set(PRODUCTS.map(p => p.category))),
];

export const MMAMASHIA_COORDS = { lat: -24.4905, lng: 26.0405 }; // Mmamashia, Botswana