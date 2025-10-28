import { z } from "zod";

export const pluginFormSchema = z.object({
    name: z.string().min(3, "Must be at least 3 characters"),
    description: z.string().min(1, "Required"),
    catalogUrl: z.url("Must be a valid URL"),
    directlyIdentifiesObjects: z.boolean(),
    pluginFile: z
        .instanceof(File, { message: "You need to provide a file" })
        .refine((f) => f.size > 0, "You need to provide a file")
        .refine((f) => /\.py$/i.test(f.name), "Only .py files are allowed"),
});

export type PluginFormValues = z.infer<typeof pluginFormSchema>;

export const pluginUpdateFormSchema = pluginFormSchema.partial();
export type PluginUpdateFormValues = z.infer<typeof pluginUpdateFormSchema>;
