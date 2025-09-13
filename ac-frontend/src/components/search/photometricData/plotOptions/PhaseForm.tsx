import {useForm} from "react-hook-form";
import {yupResolver} from "@hookform/resolvers/yup";
import {phaseFormSchema, type PhaseValues} from "@/features/search/lightcurve/schema.ts";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage} from "../../../../../components/ui/form.tsx";
import {Input} from "../../../../../components/ui/input.tsx";
import {Button} from "../../../../../components/ui/button.tsx";
import React, {useEffect} from "react";


const LabeledInput = ({label, ...props}) => {
    return (
        <div className={"flex gap-x-2 items-center"}>
            <Input className={"w-5/6"} placeholder={"12235.55"} {...props} />
            <span className={"w-1/6"}>{label}</span>
        </div>
    )
}

type PhaseFormProps = {
    epoch: number,
    period: number,
    setEpoch: React.Dispatch<React.SetStateAction<number>>,
    setPeriod: React.Dispatch<React.SetStateAction<number>>,

}

const PhaseForm = ({epoch, period, setEpoch, setPeriod}: PhaseFormProps) => {
    const form = useForm<PhaseValues>({
        resolver: yupResolver(phaseFormSchema),
        defaultValues: {
            epoch: epoch,
            period: period
        }
    });

    useEffect(() => {
        form.setValue("period", period)
        form.setValue("epoch", epoch)
    }, [epoch, period]);

    const onSubmit = (formData: PhaseValues) => {
        setEpoch(formData.epoch);
        setPeriod(formData.period);
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <h3>Phase curve parameters</h3>
                <FormField
                    control={form.control}
                    name="epoch"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Epoch</FormLabel>
                            <FormControl>
                                <LabeledInput label={""} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="period"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Period</FormLabel>
                            <FormControl>
                                <LabeledInput label={""} {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                {<p className="text-destructive text-sm">{form.formState.errors.global?.message}</p>}
                <Button type={"submit"}>Set parameters</Button>
            </form>
        </Form>
    )
}

export default PhaseForm;
