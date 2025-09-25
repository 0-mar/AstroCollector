import {useForm} from "react-hook-form";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../components/ui/form.tsx";
import {Input} from "../../../components/ui/input.tsx";
import {
    pluginUpdateFormSchema,
    type PluginUpdateFormValues
} from "@/features/plugin/schemas.ts";
import {Textarea} from "../../../components/ui/textarea.tsx";
import {Checkbox} from "../../../components/ui/checkbox.tsx";
import React from "react";
import useUpdatePlugin from "@/features/plugin/useUpdatePlugin.ts";
import {zodResolver} from "@hookform/resolvers/zod";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import type {PluginDto} from "@/features/plugin/types.ts";

type EditPluginFormProps = {
    pluginDto: PluginDto
    formId: string
    setOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const EditPluginForm = ({pluginDto, formId, setOpen}: EditPluginFormProps) => {
    const updatePluginMutation = useUpdatePlugin(pluginDto.id)

    const form = useForm<PluginUpdateFormValues>({
        resolver: zodResolver(pluginUpdateFormSchema),
        defaultValues: {
            name: pluginDto.name,
            description: pluginDto.description,
            catalogUrl: pluginDto.catalog_url,
            directlyIdentifiesObjects: pluginDto.directly_identifies_objects
        },
    })

    const onSubmit = async (formData: PluginUpdateFormValues) => {
        await updatePluginMutation.mutateAsync({
            updateData: {
                id: pluginDto.id,
                name: formData.name ?? null,
                description: formData.description ?? null,
                catalog_url: formData.catalogUrl ?? null,
                directly_identifies_objects: formData.directlyIdentifiesObjects ?? null
            },
            file: formData.pluginFile ?? null
        })
        setOpen(false)
    }

    return (
        <Form {...form}>
            <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                    control={form.control}
                    name="name"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Name</FormLabel>
                            <FormControl>
                                <Input {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="description"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Description</FormLabel>
                            <FormControl>
                                <Textarea
                                    placeholder="Catalog description"
                                    className="resize-none"
                                    {...field}
                                />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="catalogUrl"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Catalog URL</FormLabel>
                            <FormControl>
                                <Input {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="directlyIdentifiesObjects"
                    render={({ field }) => {
                        return (
                            <FormItem
                                className="flex flex-row items-center gap-2"
                            >
                                <FormControl>
                                    <Checkbox
                                        checked={field.value}
                                        onCheckedChange={(checked) => {
                                            return field.onChange(Boolean(checked))
                                        }}
                                    />
                                </FormControl>
                                <FormLabel className="text-sm font-normal">
                                    Catalog groups by stellar objects
                                </FormLabel>
                            </FormItem>
                        )
                    }}
                />
                <FormField
                    control={form.control}
                    name="pluginFile"
                    render={({ field: { value, onChange, ...fieldProps } }) => (
                        <FormItem>
                            <FormLabel>
                                New plugin source code file
                            </FormLabel>

                            <FormControl>
                                <Input
                                    {...fieldProps}
                                    type="file"
                                    accept=".py"
                                    onChange={(event) =>
                                        onChange(event.target.files && event.target.files[0])
                                    }
                                />
                            </FormControl>
                            {pluginDto.file_name !== null && <p>Current file: {pluginDto.file_name}</p>}
                            <FormMessage />
                        </FormItem>
                    )}
                />
                {updatePluginMutation.isPending && <LoadingSkeleton text={"Updating plugin..."} />}
            </form>
        </Form>
    )
}

export default EditPluginForm
