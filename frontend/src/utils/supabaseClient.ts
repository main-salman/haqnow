import { createClient } from "@supabase/supabase-js";

const supabaseUrl = "https://***REMOVED***";
// IMPORTANT: This is the anon public key and is safe to use in browser context
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh2bndpeWljd2l4ZnJib3d0amFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1MTIzMDksImV4cCI6MjA2MzA4ODMwOX0.-GfrHUPsq6ui3ZiIiFsUpbivQbLCqd61vaajEnh5I7w";

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL or anon key is missing. Check your environment configuration.");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
